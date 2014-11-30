using Neo4jClient.Cypher;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Web.Http;

namespace Neo4jDotNetDemo.Controllers
{
    [RoutePrefix("graph")]
    public class GraphController : ApiController
    {
        [HttpGet]
        [Route("{limit:int?}", Name = "getgraph")]
        public IHttpActionResult Index(int limit = 100)
        {
            //query = ("MATCH (m:Movie)<-[:ACTED_IN]-(a:Person) "
            // "RETURN m.title as movie, collect(a.name) as cast "
            // "LIMIT {limit}")

            var query = WebApiConfig.GraphClient.Cypher
                .Match("(m:Movie)<-[:ACTED_IN]-(a:Person)")
                .Return((m, a) => new
                {
                    movie = m.As<Movie>().title,
                    cast = Return.As<string>("collect(a.name)")
                })
                .Limit(limit);

            //You can see the cypher query here when debugging
            var data = query.Results.ToList();

            return Ok(data);
        }
    }

    public class Movie
    {
        public string title { get; set; }
        public int released { get; set; }
        public string tagline { get; set; }
    }
}
