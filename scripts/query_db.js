function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Content-Type': 'application/json'
  };
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders() });
    }

    const url = new URL(request.url);
    const userQuery = url.searchParams.get('query');

    if (!userQuery) {
      return new Response(JSON.stringify({ error: "No query provided." }), {
        status: 400,
        headers: corsHeaders()
      });
    }

    const trimmedQuery = userQuery.trim();
    const upperQuery = trimmedQuery.toUpperCase();

    // Allow only SELECT queries without semicolons
    if (!upperQuery.startsWith("SELECT") || upperQuery.includes(";")) {
      return new Response(JSON.stringify({ error: "Only single SELECT queries allowed." }), {
        status: 400,
        headers: corsHeaders()
      });
    }

    try {
      const result = await env.DB_READ.prepare(trimmedQuery).all();
      return new Response(JSON.stringify(result.results), { headers: corsHeaders() });
    } catch (error) {
      return new Response(JSON.stringify({ error: error.message }), {
        status: 500,
        headers: corsHeaders()
      });
    }
  },
};
