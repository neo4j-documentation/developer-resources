#!/usr/bin/env ruby
require 'rubygems'
require 'bundler/setup'
require 'logger'
require 'ascii_press'

LOGGER = Logger.new(STDOUT)

require_relative 'html_transformer' # Neo Tech specific

adoc_vars = {
  img: 'http://dev.assets.neo4j.com.s3.amazonaws.com/wp-content/uploads/',
  github: 'https://github.com/neo4j-contrib/developer-resources/tree/gh-pages',
  manual: 'http://neo4j.com/docs/stable',
  examples: 'https://github.com/neo4j-examples'
}

<<<<<<< HEAD
adoc_templates_dir = ENV['ASCIIDOC_TEMPLATES_DIR'] || '_templates'
adoc_attributes = %W(allow-uri-read linkattrs source-highlighter=codemirror) +
                    adoc_vars.map {|k, v| "#{k}=#{v}" }
=======
ASCIIDOC_TEMPLATES_DIR = ENV['ASCIIDOC_TEMPLATES_DIR'] || '_templates'
ASCIIDOC_ATTRIBUTES = %W(allow-uri-read
                         icons=font
                         linkattrs
                         source-highlighter=codemirror
                         img=#{IMAGE_BASE_URL}
                         examples=#{EXAMPLES}
                         manual=#{MANUAL}
                         github=#{GITHUB})
>>>>>>> font awesome icons for admonition notes

raise 'Usage: feed me asciidoctor files (or pass `all` to find all files)' if ARGV.empty?

renderer = AsciiPress::Renderer.new(attributes: adoc_attributes,
                                    header_footer: true,
                                    safe: 0,
                                    template_dir: adoc_templates_dir)

if ENV['BLOG_HOSTNAME'] && ENV['BLOG_USERNAME'] && ENV['BLOG_PASSWORD'] && ENV['PUBLISH']
  syncer = AsciiPress::WordPressSyncer.new(ENV['BLOG_HOSTNAME'],
                                           ENV['BLOG_USERNAME'],
                                           ENV['BLOG_PASSWORD'],
                                           renderer,
                                           post_type: 'developer',
                                           delete_not_found: false,
                                           logger: LOGGER)
end

adoc_file_paths = if ARGV == ['all']
  `find . -mindepth 2 -maxdepth 4 -name "*.adoc"`.split(/[\n\r]+/)
else
  ARGV
end

if syncer
  syncer.sync(adoc_file_paths, {})
else
  adoc_file_paths.each do |adoc_file_path|
    html_file_path = File.join(File.dirname(adoc_file_path), 'index.html')

    LOGGER.info "Rendering #{adoc_file_path} to #{html_file_path}"
    File.open(html_file_path, 'w') { |f| f << renderer.render(adoc_file_path).html }
  end
end

