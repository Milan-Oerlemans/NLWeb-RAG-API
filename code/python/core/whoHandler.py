from core.baseHandler import NLWebHandler
from core.retriever import search
from core.whoRanking import WhoRanking
from core.llm import ask_llm
from misc.logger.logging_config_helper import get_configured_logger
import asyncio

# Who handler is work in progress for answering questions about who
# might be able to answer a given query

logger = get_configured_logger("who_handler")

DEFAULT_NLWEB_ENDPOINT = "https://nlwm.azurewebsites.net/ask"
ENABLE_QUERY_FANOUT = False

class WhoHandler (NLWebHandler) :

    def __init__(self, query_params, http_handler): 
        # Remove site parameter - we'll use nlweb_sites
        if 'site' in query_params:
            del query_params['site']
            
        # Keep prev_queries if provided for context, but don't use 'prev' format
        # The who handler can use previous queries to understand follow-up questions
        if 'prev' in query_params:
            del query_params['prev']
        # Keep prev_queries for context if provided
        super().__init__(query_params, http_handler)
    
    def _build_nlweb_url(self, site_url, site_type=None):
        """Helper function to build the complete NLWEB URL with all parameters."""
        from urllib.parse import quote

        params = []
        params.append(f"site={site_url}")

        # Add the user's query
        if self.query:
            params.append(f"query={quote(self.query)}")

        # Check if it's a Shopify site and add db parameter
        if site_type in ['ShopifyStore', 'Shopify'] or 'shopify' in site_url.lower():
            params.append("db=shopify_mcp")

        # Add tool parameter to go directly to search
        params.append("tool=search")

        # Construct the full URL
        return f"{DEFAULT_NLWEB_ENDPOINT}?{'&'.join(params)}"

    async def send_message(self, message):
        """Override send_message to ensure URLs point to /ask endpoint with site parameter."""
        # Check if message contains results with URLs
        if isinstance(message, dict):
            # Handle messages with 'content' field (results)
            if 'content' in message and isinstance(message['content'], list):
                for result in message['content']:
                    if 'url' in result:
                        url = result['url']
                        # If URL doesn't start with http:// or https://, convert to /ask endpoint
                        if not url.startswith(('http://', 'https://')):
                            site_type = result.get('@type', '')
                            result['url'] = self._build_nlweb_url(url, site_type)
                            logger.debug(f"Modified URL from '{url}' to '{result['url']}'")

            # Handle single result messages
            elif 'url' in message:
                url = message['url']
                if not url.startswith(('http://', 'https://')):
                    site_type = message.get('@type', '')
                    message['url'] = self._build_nlweb_url(url, site_type)
                    logger.debug(f"Modified URL from '{url}' to '{message['url']}'")

        # Call parent class's send_message with modified message
        await super().send_message(message)

  
    async def whoQueryRewrite(self):
        ans_struc = {
          "rewritten_queries": ["query1", "query2", "query3", "query4", "query5"],
          "query_count": "Number of queries generated (1-5)"
        }
    
        prompt = f"""
        You are helping to rewrite a complex search query into simpler keyword queries for a very simple
        vector embedding search, which can easily get distracted.
        The search engine works best with short, focused queries containing important keywords.
        
        Take the following query and break it down into up to 5 simpler search queries.
        Each query should:
        - Contain no more than 3 words
        - Focus on the most important keywords and concepts
        - Be diverse to cover different aspects of the original query
        - Use only essential nouns, adjectives, or product terms
        - Avoid common words like "for", "the", "some", "are", "that", "would", "be"
        
        The original query is: {self.query}"""
        response = await ask_llm(prompt, ans_struc, level="high", 
                                query_params=self.http_handler.query_params, timeout=10)
                         
        # Extract the rewritten queries from the response
        rewritten_queries = response.get("rewritten_queries", [])

        valid_queries = [q for q in rewritten_queries if q and isinstance(q, str) and q.strip()]
        valid_queries.append(self.query)
        print(valid_queries)
        return valid_queries
    
    async def whoRetrieveInt(self, query):
        items = await search(
                query, 
                site='nlweb_sites',  # Use the sites collection
                query_params=self.query_params,
                num_results=20
            )
        for item in items:
            if (item not in self.final_retrieved_items):
                self.final_retrieved_items.append(item) 
            
  
    async def runQuery(self):

        try:
            # Send begin-nlweb-response message at the start
            await self.message_sender.send_begin_response()
            tasks = []
            if (ENABLE_QUERY_FANOUT):
                queries = await self.whoQueryRewrite()
            else:
                queries = [self.query]
            for query in queries:
                tasks.append(asyncio.create_task(self.whoRetrieveInt(query)))
            await asyncio.gather(*tasks, return_exceptions=True)       
       
            self.ranker = WhoRanking(self, self.final_retrieved_items)
            await self.ranker.do()
            
            # Send end-nlweb-response message at the end
            await self.message_sender.send_end_response()

            return [msg.to_dict() for msg in self.messages]

        except Exception as e:
            # Send end-nlweb-response even on error
            await self.message_sender.send_end_response(error=True)
            raise
        