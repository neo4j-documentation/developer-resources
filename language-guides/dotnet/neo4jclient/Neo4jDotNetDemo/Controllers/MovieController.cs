using Neo4jClient.Cypher;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Web.Http;

namespace Neo4jDotNetDemo.Controllers
{
    [RoutePrefix("movie")]
    public class MovieController : ApiController
    {
        [HttpGet]
        [Route("{title}")]
        public IHttpActionResult GetMovieByTitle(string title)
        {
            //query = ("MATCH (movie:Movie {title:{title}}) "
            // "OPTIONAL MATCH (movie)<-[r]-(person:Person) "
            // "RETURN movie.title as title,"
            // "collect([person.name, "
            // "         head(split(lower(type(r)), '_')), r.roles]) as cast "
            // "LIMIT 1")

            var data = WebApiConfig.GraphClient.Cypher
               .Match("(movie:Movie {title:{title}})")
               .OptionalMatch("(movie)<-[r]-(person:Person)")
               .WithParam("title", title)
               .Return((movie, a) => new
               {
                   movie = movie.As<Movie>().title,
                   cast = Return.As<IEnumerable<string>>("collect([person.name, head(split(lower(type(r)), '_')), r.roles])")
               })
               .Limit(1)
               .Results.FirstOrDefault();

            var result = new MovieResult();
            result.title = data.movie;

            var castresults = new List<CastResult>();
            foreach (var item in data.cast)
            {
                var tempData = JsonConvert.DeserializeObject<dynamic>(item);
                var roles = tempData[2] as JArray;
                var castResult = new CastResult
                {
                    name = tempData[0],
                    job = tempData[1],
                };
                if (roles != null)
                {
                    castResult.role = roles.Select(c => c.Value<string>());
                }
                castresults.Add(castResult);
            }
            result.cast = castresults;

            return Ok(result);
        }
    }

    public class CastResult
    {
        public string name { get; set; }
        public string job { get; set; }
        public IEnumerable<string> role { get; set; }
    }

    public class MovieResult
    {
        public string title { get; set; }
        public IEnumerable<CastResult> cast { get; set; }
    }
}
