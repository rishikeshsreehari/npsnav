export default {
    async fetch(request, env) {
      const url = new URL(request.url);
      const { pathname } = url;
  
      // Add CORS headers
      const corsHeaders = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json"
      };
  
      // Handle OPTIONS request for CORS
      if (request.method === "OPTIONS") {
        return new Response(null, {
          headers: corsHeaders
        });
      }
  
      try {
        if (pathname === "/get-last-date") {
          const fundId = url.searchParams.get("fund_id");
          const { results } = await env.DB.prepare("SELECT MAX(date) as last_date FROM fund_daily_values WHERE fund_id = ?")
                                           .bind(fundId)
                                           .all();
          return new Response(JSON.stringify(results[0]), { 
            headers: corsHeaders 
          });
        }
  
        if (pathname === "/add-nav-data") {
          const { fund_id, date, nav } = await request.json();
          await env.DB.prepare("INSERT INTO fund_daily_values (fund_id, date, nav) VALUES (?, ?, ?)")
                      .bind(fund_id, date, nav)
                      .run();
          return new Response(JSON.stringify({ status: "success" }), { 
            headers: corsHeaders 
          });
        }
  
        return new Response("Not found", { 
          status: 404,
          headers: corsHeaders 
        });
      } catch (error) {
        console.error("Error in Worker:", error);
        return new Response(JSON.stringify({ error: error.message }), { 
          status: 500,
          headers: corsHeaders 
        });
      }
    }
};