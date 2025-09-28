# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""
Simplified WHO ranking for site selection.
"""

from core.utils.utils import log
from core.llm import ask_llm
import asyncio
import json
from core.utils.json_utils import trim_json
from misc.logger.logging_config_helper import get_configured_logger
from core.schemas import create_assistant_result

logger = get_configured_logger("who_ranking_engine")

DEBUG_PRINT = False

class WhoRanking:
    
    EARLY_SEND_THRESHOLD = 59
    NUM_RESULTS_TO_SEND = 10

    def __init__(self, handler, items, level="high"): # default to high level for WHO ranking
        logger.info(f"Initializing WHO Ranking with {len(items)} items")
        self.handler = handler
        self.level = level  
        self.items = items
        self.num_results_sent = 0
        self.rankedAnswers = []

    def get_ranking_prompt(self, query, site_description):
        """Construct the WHO ranking prompt with the given query and site description."""
        prompt = f"""Assign a score between 0 and 100 to the following site based 
        the likelihood that the site will contain an answer to the user's question.
       
        First think about the kind of thing the user is seeking and then verify that the 
        site is primarily focussed on that kind of thing.

        If the user is looking to buy a product, the site should sell the product, not 
        just have useful information.
        If the user is looking for information, the site should focus on that kind of information.


The user's question is: {query}

The site's description is: {site_description}
"""
        
        response_structure = {
            "score": "integer between 0 and 100",
            "description": "short description of why this site is relevant",
            "query": "the optimized query to send to this site (only if score > 70)"
        }
        
        return prompt, response_structure

    async def rankItem(self, url, json_str, name, site):
        """Rank a single site for relevance to the query."""
        try:
            description = trim_json(json_str)
            prompt, ans_struc = self.get_ranking_prompt(self.handler.query, description)
            ranking = await ask_llm(prompt, ans_struc, level=self.level, 
                                    query_params=self.handler.query_params, timeout=8)
            
            # Ensure ranking has required fields (handle LLM failures/timeouts)
            if not ranking or not isinstance(ranking, dict):
                ranking = {"score": 0, "description": "Failed to rank", "query": self.handler.query}
            if "score" not in ranking:
                ranking["score"] = 0
            if "query" not in ranking:
                ranking["query"] = self.handler.query
            
            # Log the LLM score
            # LLM Score recorded
            
            # Handle both string and dictionary inputs for json_str
            schema_object = json_str if isinstance(json_str, dict) else json.loads(json_str)
            
            # Store the result
            ansr = {
                'url': url,
                'site': site,
                'name': name,
                'ranking': ranking,
                'schema_object': schema_object,
                'sent': False,
            }
            
            # Send immediately if high score
            if ranking.get("score", 0) > self.EARLY_SEND_THRESHOLD:
                logger.info(f"High score site: {name} (score: {ranking['score']}) - sending early")
                await self.sendAnswers([ansr])
            
            self.rankedAnswers.append(ansr)
            logger.debug(f"Site {name} added to ranked answers")
        
        except Exception as e:
            logger.error(f"Error in rankItem for {name}: {str(e)}")
            logger.debug(f"Full error trace: ", exc_info=True)
            # Still add the item with a zero score so we don't lose it completely
            try:
                schema_object = json_str if isinstance(json_str, dict) else json.loads(json_str)
                ansr = {
                    'url': url,
                    'site': site,
                    'name': name,
                    'ranking': {"score": 0, "description": f"Error: {str(e)}", "query": self.handler.query},
                    'schema_object': schema_object,
                    'sent': False,
                }
                self.rankedAnswers.append(ansr)
            except:
                pass  # Skip this item entirely if we can't even create a basic record

    async def sendAnswers(self, answers, force=False):
        """Send ranked sites to the client."""
        json_results = []
        
        for result in answers:
            # Stop if we've already sent enough
            if self.num_results_sent + len(json_results) >= self.NUM_RESULTS_TO_SEND:
                logger.info(f"Stopping at {len(json_results)} results to avoid exceeding limit of {self.NUM_RESULTS_TO_SEND}")
                break
            
            # Extract site type from schema_object
            schema_obj = result.get("schema_object", {})
            site_type = schema_obj.get("@type", "Website")
            
            result_item = {
                "@type": site_type,  # Use the actual site type
                "url": result["url"],
                "name": result["name"],
                "score": result["ranking"]["score"]
            }
            
            # Include description if available
            if "description" in result["ranking"]:
                result_item["description"] = result["ranking"]["description"]
            
            # Always include query field (required for WHO ranking)
            if "query" in result["ranking"]:
                result_item["query"] = result["ranking"]["query"]
            else:
                # Fallback to original query if no custom query provided
                result_item["query"] = self.handler.query
            
            json_results.append(result_item)
            result["sent"] = True
        
        if json_results:
            # Use the new schema to create and auto-send the message
            create_assistant_result(json_results, handler=self.handler)
            self.num_results_sent += len(json_results)
            logger.info(f"Sent {len(json_results)} results, total sent: {self.num_results_sent}/{self.NUM_RESULTS_TO_SEND}")

    async def do(self):
        """Main execution method - rank all sites concurrently."""
        
        # Create tasks for all sites
        tasks = []
        for url, json_str, name, site in self.items:
            tasks.append(asyncio.create_task(self.rankItem(url, json_str, name, site)))
        
        # Wait for all ranking tasks to complete
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error during ranking tasks: {str(e)}")
        
        # Filter and sort final results
        filtered = [r for r in self.rankedAnswers if r.get('ranking', {}).get('score', 0) > 70]
        ranked = sorted(filtered, key=lambda x: x.get('ranking', {}).get("score", 0), reverse=True)
        self.handler.final_ranked_answers = ranked[:self.NUM_RESULTS_TO_SEND]

        if (DEBUG_PRINT):
            print(f"\n=== WHO RANKING: Filtered to {len(filtered)} results with score > 70 ===")

            # Print the ranked sites with scores
            print("\nRanked sites (top 10):")
            for i, r in enumerate(ranked[:self.NUM_RESULTS_TO_SEND], 1):
                score = r.get('ranking', {}).get('score', 0)
                print(f"  {i}. {r['name']} - Score: {score}")
            print("=" * 60)

            # Print sites that were not returned
            print("\n=== SITES NOT RETURNED (sorted by score) ===")

            # Get all sites that were not included in the top 10
            not_returned_high_score = ranked[self.NUM_RESULTS_TO_SEND:]  # Sites with score > 70 but beyond top 10
            not_returned_low_score = [r for r in self.rankedAnswers if r.get('ranking', {}).get('score', 0) <= 70]

            # Sort low score sites by score (descending)
            not_returned_low_score = sorted(not_returned_low_score,
                                       key=lambda x: x.get('ranking', {}).get("score", 0),
                                       reverse=True)

            # Combine both lists
            all_not_returned = not_returned_high_score + not_returned_low_score

            if all_not_returned:
                print(f"\nTotal sites not returned: {len(all_not_returned)}")

            # Print sites with score > 70 that didn't make top 10
                if not_returned_high_score:
                    print(f"\nSites with score > 70 but beyond top {self.NUM_RESULTS_TO_SEND}:")
                    for i, r in enumerate(not_returned_high_score, 1):
                        score = r.get('ranking', {}).get('score', 0)
                        print(f"  {i}. {r['name']} - Score: {score}")

            # Print sites with score <= 70
                if not_returned_low_score:
                    print(f"\nSites with score <= 70:")
                    for i, r in enumerate(not_returned_low_score, 1):
                        score = r.get('ranking', {}).get('score', 0)
                        print(f"  {i}. {r['name']} - Score: {score}")
            else:
                print("All retrieved sites were returned to the user.")

            print("=" * 60)
        
        # Final ranked results processed
        
        # Send any remaining results that haven't been sent
        results_to_send = [r for r in ranked if not r['sent']][:self.NUM_RESULTS_TO_SEND - self.num_results_sent]
        
        if results_to_send:
            logger.info(f"Sending final batch of {len(results_to_send)} results")
            await self.sendAnswers(results_to_send, force=True)