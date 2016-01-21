require 'rubypress'
require 'logger'

class WordPressSyncer
  def initialize(blog_id, username, password, options = {})
    @blog_id = blog_id
    @wp_client = Rubypress::Client.new(host: @blog_id, username: username, password: password)
    @post_type = options[:post_type] || 'developer'
    @logger = options[:logger] || Logger.new(STDOUT)

    @all_pages = @wp_client.getPosts(filter: {post_type: @post_type, number: 1000})
    @logger.info "Got #{@all_pages.length} pages from the database"
  end

  def sync(title, post_name, html, custom_fields = {})
    content = {
                post_type:     @post_type,
                post_date:     Time.now - 60*60*24*30,
                post_content:  html,
                post_title:    title,
                post_name:     post_name,
                post_status:   'publish',
                custom_fields: custom_fields
              }

    pages = @all_pages.select { |page| page['post_name'] == post_name }
    @logger.info "Got #{pages.length} pages matching the post_name '#{post_name}'"

    page = pages.sort_by {|hash| hash['post_id'].to_i }.first

    if page
      if page['custom_fields']
        content[:custom_fields].each do |f|
          found = page['custom_fields'].find { |field| field['key'] == f[:key] }
          f['id'] = found['id'] if found
        end
      end

      post_id = page['post_id'].to_i

      @logger.info "Editing #{post_id} on _#{@blog_id}_ custom-field #{content[:custom_fields].inspect}"

      send_message(:editPost, blog_id: @blog_id, post_id: post_id, content: content)
    else
      @logger.info "Making a new post for '#{title}' on _#{@blog_id}_"

      send_message(:newPost, blog_id: @blog_id, content: content)
    end
  end

  private

  def send_message(message, *args)
    @wp_client.send(message, *args).tap do |result|
      raise "WordPress #{message} failed!" if !result
    end
  end
end






