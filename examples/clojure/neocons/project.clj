(defproject neocons-example "0.1.0-SNAPSHOT"
  :description "FIXME: write description"
  :url "http://example.com/FIXME"
  :dependencies [[org.clojure/clojure "1.6.0"]
                 [compojure "1.1.8"]
                 [clojurewerkz/neocons "3.0.0"]
                 [ring/ring-json "0.3.1"]]
  :plugins [[lein-ring "0.8.11"]]
  :ring {:handler neocons-example.handler/app}
  :profiles {:dev {:dependencies [[javax.servlet/servlet-api "2.5"]
                                  [ring-mock "0.1.5"]]}})
