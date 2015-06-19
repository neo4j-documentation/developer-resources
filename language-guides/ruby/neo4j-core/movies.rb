require 'sinatra'
require 'neo4j-core'
set :root, File.dirname(__FILE__)
set :public_folder, File.dirname(__FILE__) + '/static'

neo4j_url = ENV['NEO4J_URL'] || 'http://localhost:7474'
neo4j_username = ENV['NEO4J_USERNAME'] || 'neo4j'
neo4j_password = ENV['NEO4J_PASSWORD'] || 'neo4j'

session = Neo4j::Session.open(:server_db, neo4j_url, basic_auth: {username: neo4j_username, password: neo4j_password})

get '/' do
  send_file File.expand_path('index.html', settings.public_folder)
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
    # puts "results #{row}"
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

get "/search" do
  puts "query #{request[:q]}"
  query = "MATCH (movie:Movie) WHERE movie.title =~ {title} RETURN movie.title as title, movie.released as released, movie.tagline as tagline"
  response = session.query(query, title: "(?i).*#{request[:q]}.*")
  results = []
  response.each do |row|
    results << {
        "movie" => {
            "title" => row[:title],
            "released" => row[:released],
            "tagline" => row[:tagline]
        }
    }
  end
  results.to_json
end

get "/movie/:movie" do
  puts "movie #{params['movie']}"
  query = "MATCH (movie:Movie {title:{title}}) OPTIONAL MATCH (movie)<-[r]-(person:Person) RETURN movie.title as title, collect([person.name, head(split(lower(type(r)), '_')), r.roles]) as cast LIMIT 1"
  response = session.query(query, title: params['movie'])
  row = response.next
  puts row.to_json
  cast = []
  row[:cast].each do |c|
    cast << {
        "name" => c[0],
        "job" => c[1],
        "role" => c[2]
    }
  end
  result = {
      "title" => row[:title],
      "cast" => cast
  }
  result.to_json

end

