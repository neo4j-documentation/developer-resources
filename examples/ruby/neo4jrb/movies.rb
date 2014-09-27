require 'sinatra'
require 'neo4j'
require 'models'

set :public_folder, File.dirname(__FILE__) + '/static'

session = Neo4j::Session.open

get '/' do
  redirect '/index.html'
end

get '/graph' do
  Movie.all.each do |movie|
      puts movie.actors # TODO
  end
  ""
end