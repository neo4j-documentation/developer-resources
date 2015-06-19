require 'sinatra'
require 'neo4j'
require './models'

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
  actors = Person.all.to_a # or if we want to be sure, query_as(:p).match("p-[:ACTED_IN]->()").pluck('distinct p')
  movies = Movie.all.to_a

  nodes = actors + movies
  links = movies.map.with_index(2).to_a.map do |movie_and_index|
    movie_and_index[0].actors.map do |a|
      {source: movie_and_index[1], target: nodes.index(a)}
    end
  end.flatten

  nodes_hash = actors.map{|n| {title: n.name, label: "actor"}} + movies.map{|n| {title: n.title, label: "movie"}}

  {nodes: nodes_hash, links:links}.to_json
end

get '/search' do
  movies = Movie.where(title: /.*#{request['q']}.*/i)

  movies.map {|movie| {movie: movie.attributes} }.to_json
end

get '/movie/:title' do
  movie = Movie.where(title: params['title']).first

  cast_data_for_role = Proc.new do |role|
    Proc.new do |person, rel|
      {
        name: person.name,
        # we could have used the roles accessor (rel.roles) method here when rol is a Engagement class
        role: rel.props[:roles] || [],  
        job: role
      }
    end
  end

  cast_data = movie.actors.each_with_rel.map(&cast_data_for_role.call(:acted)) +
              movie.directors.each_with_rel.map(&cast_data_for_role.call(:directed))

  {title: movie.title, cast: cast_data}.to_json
end

