require File.join(File.dirname(__FILE__), 'movies')

map "/index.html" do
  run Rack::File.new("./static/index.html")
end

run Sinatra::Application
