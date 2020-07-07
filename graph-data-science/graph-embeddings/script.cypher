CALL gds.alpha.node2vec.write({
  nodeProjection: "Character",
  relationshipProjection: {s1: {type: "INTERACTS_SEASON1", orientation: "UNDIRECTED"} },
  embeddingSize: 2,
  iterations: 3,
  writeProperty: "node2vec"
});

CALL gds.alpha.randomProjection.write({
  nodeProjection: "Character",
  relationshipProjection: {s1: {type: "INTERACTS_SEASON1", orientation: "UNDIRECTED"} },
  embeddingSize: 2,
  maxIterations: 3,
  writeProperty: "fastrp"
});

CALL gds.alpha.graphSage.write({
  nodeProjection: "Character",
  relationshipProjection: {s1: {type: "INTERACTS_SEASON1", orientation: "UNDIRECTED"} },
  embeddingSize: 2,
  maxIterations: 3,
  degreeAsProperty: true,
  writeProperty: "graphSage"
});

match (c:Character {id: "JON"})
match (other:Character) WHERE other <> c
WITH c, other, gds.alpha.similarity.cosine(c.node2vec, other.node2vec) AS node2Vec
ORDER By node2Vec DESC
WITH c, collect([other.id, node2Vec])[0] AS closestNode2vec
match (other:Character) WHERE other <> c
WITH c, other, closestNode2vec, gds.alpha.similarity.cosine(c.fastrp, other.fastrp) AS fastrp
ORDER BY fastrp DESC
WITH c, closestNode2vec, collect([other.id, fastrp])[0] AS closestFastRP
match (other:Character) WHERE other <> c
WITH c, other, closestNode2vec, closestFastRP, gds.alpha.similarity.cosine(c.graphSage, other.graphSage) AS graphSage
ORDER BY graphSage DESC
WITH c, closestNode2vec, closestFastRP, collect([other.id, graphSage])[0] AS closestGraphSage
RETURN c.id, closestFastRP, closestNode2vec, closestGraphSage;


CALL gds.alpha.randomProjection.write({
  nodeProjection: "*",
  relationshipProjection: "*",
  embeddingSize: 10,
  maxIterations: 1,
  writeProperty: "fastrp"
});

CALL gds.alpha.node2vec.write({
  nodeProjection: "*",
  relationshipProjection: "*",
  embeddingSize: 10,
  iterations: 1,
  writeProperty: "node2vec"
});

match (r:Recipe {id: "101233"})
match (other:Recipe)
WHERE r <> other
RETURN r.fastrp, other.fastrp, other.name, gds.alpha.similarity.cosine(r.fastrp, other.fastrp) AS similarity
ORDER BY similarity DESC
LIMIT 10;
