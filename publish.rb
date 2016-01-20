#!/usr/bin/env ruby
require 'rubygems'
require 'bundler/setup'
require 'logger'
require 'asciidoctor'
require 'pathname'

IMAGE_BASE_URL = 'http://dev.assets.neo4j.com.s3.amazonaws.com/wp-content/uploads/'
GITHUB = 'https://github.com/neo4j-contrib/developer-resources/tree/gh-pages'
MANUAL = 'http://neo4j.com/docs/stable'
EXAMPLES = 'https://github.com/neo4j-examples'

ASCIIDOC_TEMPLATES_DIR = ENV['ASCIIDOC_TEMPLATES_DIR'] || '_templates'
ASCIIDOC_ATTRIBUTES = %W(allow-uri-read
                         linkattrs
                         source-highlighter=codemirror
                         img=#{IMAGE_BASE_URL}
                         examples=#{EXAMPLES}
                         manual=#{MANUAL}
                         github=#{GITHUB})

require_relative('html_transformer')
require_relative('word_press_syncer')

logger = Logger.new(STDOUT)
syncer = WordPressSyncer.new(ENV['BLOG_HOSTNAME'], ENV['BLOG_USERNAME'], ENV['BLOG_PASSWORD'], logger: logger)

raise 'Usage: feed me asciidoctor files' if ARGV.empty?

ARGV.each do |adoc_file_path|
  adoc = Asciidoctor.load_file(adoc_file_path,
                               template_dir: ASCIIDOC_TEMPLATES_DIR, header_footer: true, attributes: ASCIIDOC_ATTRIBUTES)

  html = adoc.convert

  data = {}

  post_name = File.basename(adoc_file_path, '.*')
  optional_slug = adoc.attributes['slug'].to_s
  post_name = optional_slug unless optional_slug.empty?

  %w(level author email).each do |key|
    data[key.to_sym] = adoc.attributes[key]
  end

  data[:developer_section_name] = adoc.attributes['section'].to_s
  # data[:developer_section_slug] = adoc.attributes['section-link']

  data.reject! {|_, value| value.nil? }

  html = adoc.convert

  logger.info "publishing: #{adoc.doctitle} (post_name: #{post_name})"

  # logger.info "data: #{data.inspect}"

  syncer.sync(adoc.doctitle, post_name, html,
              [{key: 'developer_section_name', value: data[:developer_section_name]},
               {key: 'developer_section_slug', value: ''}]) # was data[:developer_section_slug]
end

