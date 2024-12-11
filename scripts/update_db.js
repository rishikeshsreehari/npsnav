// Add CORS headers helper function
function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Content-Type': 'application/json'
  };
}

export default {
  async fetch(request, env) {
    // Handle OPTIONS request for CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: corsHeaders()
      });
    }

    // Log the AUTH_TOKEN from wrangler.toml (environment variable)
    console.log("Token from wrangler.toml (env.AUTH_TOKEN):", env.AUTH_TOKEN);

    const authToken = request.headers.get('Authorization');

    // Log the Authorization header from the request
    console.log("Authorization header from request:", authToken);

    // If the Authorization header does not match the token from wrangler.toml
    if (authToken !== `Bearer ${env.AUTH_TOKEN}`) {
      console.log("Authorization failed: Token mismatch");
      return new Response(JSON.stringify({ error: 'Unauthorized' }), { 
        status: 401,
        headers: corsHeaders()
      });
    }

    const { pathname } = new URL(request.url);

    try {
      if (pathname.startsWith('/latest-fund')) {
        return getLatestFund(env, request);
      } else if (pathname.startsWith('/latest-nifty')) {
        return getLatestNifty(env);
      } else if (pathname.startsWith('/update-fund')) {
        return updateFund(env, request);
      } else if (pathname.startsWith('/update-nifty')) {
        return updateNifty(env, request);
      } else {
        return new Response('Not found', { 
          status: 404,
          headers: corsHeaders()
        });
      }
    } catch (error) {
      console.log("Error occurred:", error);
      return new Response(JSON.stringify({ error: error.message }), { 
        status: 500,
        headers: corsHeaders()
      });
    }
  },
};

async function getLatestFund(env, request) {
  const url = new URL(request.url);
  const fundId = url.searchParams.get('fund_id');

  if (!fundId) {
    return new Response(JSON.stringify({ error: 'fund_id is required' }), { 
      status: 400,
      headers: corsHeaders()
    });
  }

  try {
    const query = `
      SELECT date, nav FROM fund_daily_values
      WHERE fund_id = ?
      ORDER BY date DESC LIMIT 1;
    `;

    const result = await env.DB_WRITE.prepare(query).bind(fundId).first();
    return new Response(JSON.stringify(result || { date: null, nav: null }), { 
      headers: corsHeaders() 
    });
  } catch (error) {
    console.log("Error fetching latest fund:", error);
    return new Response(JSON.stringify({ error: error.message }), { 
      status: 500,
      headers: corsHeaders()
    });
  }
}

async function getLatestNifty(env) {
  try {
    const query = `
      SELECT date, nav FROM nifty_daily_values
      ORDER BY date DESC LIMIT 1;
    `;

    const result = await env.DB_WRITE.prepare(query).first();
    return new Response(JSON.stringify(result || { date: null, nav: null }), { 
      headers: corsHeaders() 
    });
  } catch (error) {
    console.log("Error fetching latest nifty:", error);
    return new Response(JSON.stringify({ error: error.message }), { 
      status: 500,
      headers: corsHeaders()
    });
  }
}

async function updateFund(env, request) {
  try {
    const { fund_id, date, nav } = await request.json();

    if (!fund_id || !date || !nav) {
      return new Response(JSON.stringify({ error: 'fund_id, date, and nav are required' }), { 
        status: 400,
        headers: corsHeaders()
      });
    }

    const query = `
      INSERT OR REPLACE INTO fund_daily_values (fund_id, date, nav)
      VALUES (?, ?, ?);
    `;

    await env.DB_WRITE.prepare(query).bind(fund_id, date, nav).run();
    return new Response(JSON.stringify({ success: true }), { 
      headers: corsHeaders() 
    });
  } catch (error) {
    console.log("Error updating fund:", error);
    return new Response(JSON.stringify({ error: error.message }), { 
      status: 500,
      headers: corsHeaders()
    });
  }
}

async function updateNifty(env, request) {
  try {
    const { date, nav } = await request.json();

    if (!date || !nav) {
      return new Response(JSON.stringify({ error: 'date and nav are required' }), { 
        status: 400,
        headers: corsHeaders()
      });
    }

    const query = `
      INSERT OR REPLACE INTO nifty_daily_values (date, nav)
      VALUES (?, ?);
    `;

    await env.DB_WRITE.prepare(query).bind(date, nav).run();
    return new Response(JSON.stringify({ success: true }), { 
      headers: corsHeaders() 
    });
  } catch (error) {
    console.log("Error updating nifty:", error);
    return new Response(JSON.stringify({ error: error.message }), { 
      status: 500,
      headers: corsHeaders()
    });
  }
}
