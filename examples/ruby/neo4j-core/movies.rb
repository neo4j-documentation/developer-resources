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
  nodes = []
  rels = []

  i = 0
  session.query(query).each do |record|
    nodes.push({
                   "title" => record.movie,
                   "label" => "movie"
               })
    target = i
    i +=1
    record.cast.each do |c|
      actor = {
          "title" => c,
          "label" => "actor"
      }
      k = 0
      source = -1
      nodes.each do |a|
        if (a['title'] == actor['title'])
          source = k
        end
        k +=1
      end
      if source == -1
        nodes.push(actor)
        source = i
        i += 1
      end
      rels.push({
                    "source" => source,
                    "target" => target
                })
    end
  end

  result = {
      "nodes" => nodes,
      "links" => rels
  }

  puts "RESULT #{result}"
  result.to_json
end