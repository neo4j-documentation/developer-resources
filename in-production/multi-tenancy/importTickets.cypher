// tag::params[]
:param params => { url: {url}, mall: {mall}}
// end::params[]

// tag::query[]

CALL apoc.periodic.iterate(
  "CALL apoc.load.json($url)
   YIELD value
   WHERE value.mall = $mall
   RETURN value
   LIMIT 10000",
  "CREATE (t:Ticket {id: value._id, datetime: datetime(value.date)})
   MERGE (c:Client {id: value.client})
   CREATE (c)<-[:PURCHASED_BY]-(t)
   WITH value, t
   UNWIND value.items as item
   CREATE (t)-[:HAS_TICKETITEM]->(ti:TicketItem {
     product: item.desc,
     netamount: item.net_am,
     numberofunits: item.n_unit
   })
   MERGE (p:Product {description: item.desc})
   CREATE (ti)-[:FOR_PRODUCT]->(p)",
  { batchSize: 10000,
    iterateList: true,
    parallel: false,
    params: $params}
);
// end::query[]
