require 'sinatra'
require 'neo4j-core'
set :root, File.dirname(__FILE__)

session = Neo4j::Session.open

get '/' do
  redirect '/index.html'
end

get '/graph' do
  puts "QUERY"
  query = """
    MATCH (m:Movie)<-[:ACTED_IN]-(a:Person)
    RETURN m.title as movie, collect(a.name) as cast
    LIMIT {limit}
  """

  movies_and_casts = session.query(query, limit: params[:limit] || 50)

  nodes = []
  rels = []
  i = 0
  movies_and_casts.each do |row|
    nodes << {title: row.movie, label: 'movie'}
    target = i
    i += 1
    row.cast.each do |name|
      actor = {title: name, label: "actor"}
      source = nodes.index(actor)
      unless source
        source = i
        nodes << actor
        i+=1
      end
      rels << {source: source, target: target}
    end

  end
  {nodes: nodes, links: rels}.to_json

end
