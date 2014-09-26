require 'sinatra'

require 'neo4j-core'
set :public_folder, File.dirname(__FILE__) + '/static'


session = Neo4j::Session.open
get '/' do
  redirect to('/index.html')
end

get '/graph' do
  query = "MATCH (m:Movie)<-[:ACTED_IN]-(a:Person) " +
  "RETURN m.title as movie, collect(a.name) as cast " +
  "LIMIT 10"

  result = session.query(query).map(&:cast)

  puts "RESULT #{result}"
  result.to_json
end