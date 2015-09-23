#!/usr/bin/env ruby
require 'rubygems'
require 'bundler/setup'

require 'html_transformer'
RSpec.describe HtmlTransformer do
  it "renders original links correctly" do
    fragment = [%{ <dd class="accordion-navigation inactive">},
                %{ <a href="/developer/cypher">\n},
                %{ <h5>Cypher Query Language</h5>}]

    expect(HtmlTransformer.transform(fragment)).to match('<a href=\"/developer/cypher\">')
  end

  it "renders links with a trailing slash correctly" do 
    fragment = [%{<dd class="accordion-navigation active">},
                %{<a href="/developer/language-guides/">},
                %{<h5>Language Guides</h5>},
                %{ </a> }]
    expect(HtmlTransformer.transform(fragment)).to match('<a href=\"/developer/language-guides/">')

  end
end
