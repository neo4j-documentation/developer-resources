class Engagement
  include Neo4j::ActiveRel
  property :roles  # this contains an array of roles
  from_class 'Person'
  to_class 'Movie'
  type :ACTED_IN
end

class Movie
  include Neo4j::ActiveNode
  id_property :title
  property :released
  property :tagline
  has_many :in, :actors, model_class: :Person, rel_class: 'Engagement'
  has_many :in, :directors, model_class: :Person, type: :DIRECTED
end

class Person
  include Neo4j::ActiveNode
  id_property :name
  has_many :out, :acted_in, model_class: :Movie, rel_class: 'Engagement'
  has_many :out, :directed, model_class: :Movie, type: :DIRECTED
end

