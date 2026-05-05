LOAD CSV WITH HEADERS FROM 'file:///place_nodes.csv' AS row
MERGE (p:Place {place_id: row.`node_id:ID(Place)`})
SET p.name = row.name, p.category = row.category, p.rating = toFloat(row.rating), p.total_user_ratings = toInteger(row.total_user_ratings), p.formatted_address = row.formatted_address, p.google_maps_url = row.google_maps_url;

LOAD CSV WITH HEADERS FROM 'file:///user_nodes.csv' AS row
MERGE (u:User {user_id: row.`node_id:ID(User)`})
SET u.name = row.name;

LOAD CSV WITH HEADERS FROM 'file:///reviewed_edges.csv' AS row
MATCH (u:User {user_id: row.`:START_ID(User)`})
MATCH (p:Place {place_id: row.`:END_ID(Place)`})
MERGE (u)-[r:REVIEWED]->(p)
SET r.rating = toFloat(row.rating), r.review_text = row.review_text;

LOAD CSV WITH HEADERS FROM 'file:///place_edges.csv' AS row
MATCH (p1:Place {place_id: row.`:START_ID(Place)`})
MATCH (p2:Place {place_id: row.`:END_ID(Place)`})
MERGE (p1)-[r:CO_VISITED]->(p2)
SET r.weight = toInteger(row.weight);

LOAD CSV WITH HEADERS FROM 'file:///user_edges.csv' AS row
MATCH (u1:User {user_id: row.`:START_ID(User)`})
MATCH (u2:User {user_id: row.`:END_ID(User)`})
MERGE (u1)-[r:SIMILAR_USER]->(u2)
SET r.weight = toInteger(row.weight);