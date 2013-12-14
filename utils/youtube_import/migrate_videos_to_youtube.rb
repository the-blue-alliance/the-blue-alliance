#!/usr/bin/ruby
require "json"
require "youtube_it"
require 'yaml'

cnf = YAML::load_file(File.join(File.dirname(File.expand_path(__FILE__)), 'config.yml'))
key = cnf["key"]
client = YouTubeIt::Client.new(:dev_key => key, :username => cnf["username"], :password => cnf["password"])
STATUS_FILE_PATH = "youtube_status.json"

# read status
puts "Inspecting video directory... This may take a second or two..."
files = Dir["/storage/videos/**/**"].select{ |f| f.end_with?(".flv", ".wmv", ".mp4")}
ignore = ["2011new"]

videos = files.map { |f|
	f_name = f.split("/").last
	event = f.split("/")[-2]
	{
		:path => f,
		:event => event,
		:match => f_name.split("_").last.split(".").first,
		:type => f_name.split("_").last.split(".").last,
		:file => f_name,
		:full_match => f_name.split(".").first
	}
}.select {|v| !ignore.include?(v[:event])}

status_dir = "/home/tba/scripts/youtube_status"
done_dir = "/home/tba/scripts/youtube_done"

playlists = client.playlists
videos.each do |v| 
	title = "#{v[:event].upcase} - #{v[:match].upcase}"
	event = v[:event].upcase
	st_file = "#{status_dir}/#{v[:event]}-#{v[:file]}"
	done_file = "#{done_dir}/#{v[:event]}-#{v[:file]}"
	f = File.exist?(st_file)
	done = f ? File.read(st_file).start_with?("done") : false
	if !done
		File.write(st_file, "started\n")
		puts "Uploading... ", title
		tba_link = "http://www.thebluealliance.com/match/#{v[:full_match]}"
		puts tba_link
		video = client.video_upload(File.open(v[:path]), :title => title ,:description => "FIRST Robotics Competition match video: #{title}\n#{tba_link}", :category => 'Sports',:keywords => %w[frc omgrobots thebluealliance])
		puts "Done uploading video!"
		puts video.video_id
		in_pl = false
		pl_index = 0
		while !in_pl

			pl = nil
			event_pl = event + (pl_index > 0  ? "_#{pl_index}" : "")
			puts "Trying to add to playlist #{event_pl}"
			if !playlists.map(&:title).include?(event_pl)
				pl = client.add_playlist(:title => event, :description => "Match videos from #{event}")
				playlists = client.playlists
			else
				pl = playlists.find{|x| x.title == event_pl}
			end

			begin
				if pl
					client.add_video_to_playlist(pl.playlist_id, video.video_id)
					in_pl = true
				end
			rescue
				puts "#{event_pl} is probably full..."
			ensure
				pl_index += 1
			end

			if pl_index > 5
				in_pl = true #eff it
			end
		end
		File.write(st_file, "done\n")
		File.write(done_file, video.video_id)
	else
		puts "Skipping", title
	end
end

puts "DONE UPLOADING!"

