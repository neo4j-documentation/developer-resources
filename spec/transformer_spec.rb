#!/usr/bin/env ruby
require 'rubygems'
require 'bundler/setup'

require './html_transformer'
RSpec.describe HtmlTransformer do
  describe '.transform' do
    subject { HtmlTransformer.transform(fragment.split(/\s*[\n\r]\s*+/)) }

    context 'original links' do
      let(:fragment) do
        <<-FRAGMENT
        <dd class="accordion-navigation inactive">
        <a href="/developer/cypher">
        <h5>Cypher Query Language</h5>
        FRAGMENT
       end

       it { should match('<a href=\"/developer/cypher\">') }
    end

    context "links with a trailing slash" do
      let(:fragment) do
        <<-FRAGMENT
          <dd class="accordion-navigation active">
          <a href="/developer/language-guides/">
          <h5>Language Guides</h5>
          </a>
        FRAGMENT
      end

      it { should match('<a href=\"/developer/language-guides/">') }
    end

    context "developer-resources links" do
      let(:fragment) do
        <<-FRAGMENT
          <dd class="accordion-navigation active">
          <a href="/developer/language-guides/">
          <h5>Language Guides</h5>
          </a>
        FRAGMENT
      end

      it { should match('<a href=\"/developer/language-guides/">') }
    end

    context 'multiple links' do
      let(:fragment) do
        <<-FRAGMENT
          <li><a href="/developer/in-production/guide-cloud-deployment/">Guide: Cloud Deployment</a></li>
          <li><a href="/developer/in-production/guide-sizing-and-hardware-calculator/">Sizing + Hardware Calculator</a></li>
          <li><a href="/developer/in-production/guide-performance-tuning/">Performance Tuning</a></li>
          <li><a href="/developer/in-production/guide-clustering-neo4j/">Clustering Neo4j </a></li>
        FRAGMENT
      end

      it { should match ('/developer/guide-clustering-neo4j') }
    end
  end
end
