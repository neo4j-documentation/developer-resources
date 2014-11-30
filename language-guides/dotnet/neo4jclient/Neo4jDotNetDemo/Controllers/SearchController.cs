using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Web.Http;

namespace Neo4jDotNetDemo.Controllers
{
    [RoutePrefix("search")]
    public class SearchController : ApiController
    {
        [HttpGet]
        [Route("")]
        public IHttpActionResult SearchMoviesByTitle(string q)
        {
            //    query = ("MATCH (movie:Movie) "
            //         "WHERE movie.title =~ {title} "
            //         "RETURN movie")
            //    params={"title": "(?i).*" + q + ".*"}

            var data = WebApiConfig.GraphClient.Cypher
               .Match("(m:Movie)")
               .Where("m.title =~ {title}")
               .WithParam("title", "(?i).*" + q + ".*")
               .Return<Movie>("m")
               .Results.ToList();

            return Ok(data.Select(c => new { movie = c}));
        }
    }
}
