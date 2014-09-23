require 'open-uri'
require 'json'
require 'csv'

API_KEY = ENV['MOVIE_DB_KEY']

CSV.open("all-movies.csv", 'wb') do |f|
  f << ["Title", "Id", "ReleaseDate"]
  (1..10).each do |page|
    content = open("http://api.themoviedb.org/3/movie/popular?api_key=#{API_KEY}&page=#{page}").read

    result = JSON.parse(content)

    result["results"].each do |movie|
      f << [movie["original_title"], movie["id"], movie["release_date"]]
    end
  end
end
