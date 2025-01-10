import json
from collections import defaultdict
from typing import List, Optional

import requests

from chat.service import ChatService
from puzzles.puzzle_tag import PuzzleTag

DISCORD_BASE_API_URL = "https://discord.com/api"

CHANNEL_CATEGORY_TYPE = 4
CHANNEL_TEXT_TYPE = 0
CHANNEL_VOICE_TYPE = 2
CHANNEL_FORUM_TYPE = 15

class DiscordChatService(ChatService):
    """Discord service proxy.

    This interface implementation should be registered in Django settings under DISCORD

    """

    def __init__(self, settings, max_channels_per_category=50):
        """Accepts Django settings object and optional Discord APIClient (for testing)."""
        self._headers = {
            "Authorization": f"Bot {settings.DISCORD_API_TOKEN}",
            "Content-Type": "application/json",
        }
        self._max_channels_per_category = max_channels_per_category

    def _make_link_embeds(self, embedded_urls):
        if not embedded_urls:
            return None
        fields = [
            {
                "name": text,
                "value": f"[link]({url})",
                "inline": True,
            }
            for text, url in embedded_urls.items()
        ]
        if not len(fields):
            return None
        # 12852794 is Cardinal
        return [{"fields": fields, "color": 12852794, "type": "rich"}]

    def send_message(self, channel_id, msg, embedded_urls={}):
        """
        Edits forum post identified by channel_id.
        embedded_urls is a map mapping display_text to url.
        e.g. { "Join voice channel": "https://discord.gg/XXX" }
        """
        try:
            embeds = self._make_link_embeds(embedded_urls)
            requests.patch(
                f"{DISCORD_BASE_API_URL}/channels/{channel_id}",
                headers=self._headers,
                json={"content": msg, "embeds": embeds},
                timeout=5,
            )
        except Exception as e:
            print(f"Error sending message to discord forum post: {e}")

    def announce(self, puzzle_announcements_id, msg, embedded_urls={}):
        if puzzle_announcements_id:
            self.send_message(puzzle_announcements_id, msg, embedded_urls)
        return

    # Forum-related methods:

    def create_forum_channel(self, guild_id, forum_name):
        """Creates a new forum channel in the guild."""
        if not guild_id:
            raise Exception("Missing guild_id")

        return self._create_channel_impl(
            guild_id, forum_name, chan_type=CHANNEL_FORUM_TYPE
        )

    def _get_or_create_forum_channel(self, guild_id, forum_name):
        """
        Returns id for forum channel. If it doesn't exist, a new one is created.
        """
        all_channels = self._get_channels_for_guild(guild_id)
        forum_channels = [
            c
            for c in all_channels
            if c["name"] == forum_name and c["type"] == CHANNEL_FORUM_TYPE
        ]

        if len(forum_channels) > 0:
            return forum_channels[0]["id"]

        return self.create_forum_channel(guild_id, forum_name)

    def create_forum_post(
        self, forum_channel_id, puzzle_name, content, tag_ids, puzzle
    ):
        """Creates a new post in the specified forum channel."""
        try:
            applied_tags = []
            if tag_ids is not None:
                applied_tags = [str(tag_id) for tag_id in tag_ids]
            response = requests.post(
                f"{DISCORD_BASE_API_URL}/channels/{forum_channel_id}/threads",
                headers=self._headers,
                json={
                    "name": puzzle_name,
                    "message": {
                        "content": content,
                        "embeds": self._make_link_embeds(
                            puzzle.create_field_url_map()
                        ),
                    },
                    "applied_tags": applied_tags,
                },
                timeout=5,
            )
            json_dict = json.loads(response.content.decode("utf-8"))
            if "id" in json_dict:
                thread_id = json_dict["id"]
                thread_url = self.create_channel_url(
                    self.get_guild_id(puzzle), thread_id
                )
                return thread_id, thread_url
            print(f"Unable to create forum post for {puzzle_name}")
        except Exception as e:
            print(f"Error creating forum post: {e}")

    def edit_forum_post(self, post_id, new_content, embedded_urls):
        """Updates the content of a forum post."""
        self.send_message(post_id, new_content, embedded_urls)

    def add_tag_to_post(self, post_id, tag_id):
        """Adds a tag to a forum post."""
        if tag_id is None:
            return
        try:
            response = requests.get(
                f"{DISCORD_BASE_API_URL}/channels/{post_id}",
                headers=self._headers,
                timeout=5,
            )
            json_dict = json.loads(response.content.decode("utf-8"))
            applied_tags = []
            if "applied_tags" in json_dict:
                applied_tags = json_dict["applied_tags"]

            if str(tag_id) not in applied_tags:
                applied_tags.append(str(tag_id))
                requests.patch(
                    f"{DISCORD_BASE_API_URL}/channels/{post_id}",
                    headers=self._headers,
                    json={"applied_tags": applied_tags},
                    timeout=5,
                )

        except Exception as e:
            print(f"Error adding tag to post: {e}")

    def remove_tag_from_post(self, post_id, tag_id):
        """Removes a tag from a forum post."""
        if tag_id is None:
            return
        try:
            response = requests.get(
                f"{DISCORD_BASE_API_URL}/channels/{post_id}",
                headers=self._headers,
                timeout=5,
            )
            json_dict = json.loads(response.content.decode("utf-8"))
            applied_tags = []
            if "applied_tags" in json_dict:
                applied_tags = json_dict["applied_tags"]

            if str(tag_id) in applied_tags:
                applied_tags.remove(str(tag_id))
                requests.patch(
                    f"{DISCORD_BASE_API_URL}/channels/{post_id}",
                    headers=self._headers,
                    json={"applied_tags": applied_tags},
                    timeout=5,
                )
        except Exception as e:
            print(f"Error removing tag from post: {e}")

    def edit_forum_post_name(self, post_id, new_name):
        """Renames a forum post."""
        try:
            requests.patch(
                f"{DISCORD_BASE_API_URL}/channels/{post_id}",
                headers=self._headers,
                json={"name": new_name},
                timeout=5,
            )
        except Exception as e:
            print(f"Error renaming forum post: {e}")

    # Methods no longer used (or significantly modified):

    def create_text_channel(self, guild_id, name, text_category_name="text"):
        raise NotImplementedError("Use create_forum_channel instead")

    def get_text_channel_participants(self, channel_id):
        return []  # Not applicable to forum posts

    def delete_text_channel(self, channel_id):
        pass  # Not implemented

    def create_audio_channel(self, guild_id, name, voice_category_name="voice"):
        raise NotImplementedError("Audio channels are not used")

    def delete_audio_channel(self, channel_id):
        pass  # Not implemented

    def delete_channel(self, channel_id):
        pass  # Not implemented

    def _create_channel_impl(self, guild_id, name, chan_type, parent_id=None):
        """
        Returns channel id
        """
        try:
            response = requests.post(
                f"{DISCORD_BASE_API_URL}/guilds/{guild_id}/channels",
                headers=self._headers,
                json={"name": name, "type": chan_type, "parent_id": parent_id},
                timeout=5,
            )
            json_dict = json.loads(response.content.decode("utf-8"))
            if "id" in json_dict:
                return json_dict["id"]
            print(f"Unable to create channel")
        except Exception as e:
            print(f"Error creating channel: {e}")

    def _modify_channel_parent(self, channel_id, parent_id):
        raise NotImplementedError("Not applicable to forum posts")

    def categorize_channel(self, guild_id, channel_id, category_name):
        raise NotImplementedError("Not applicable to forum posts")

    def archive_channel(self, guild_id, channel_id, discord_archive_category="archive"):
        raise NotImplementedError("Not applicable to forum posts")

    def unarchive_text_channel(self, guild_id, channel_id, text_category_name="text"):
        raise NotImplementedError("Not applicable to forum posts")

    def unarchive_voice_channel(
        self, guild_id, channel_id, voice_category_name="voice"
    ):
        raise NotImplementedError("Not applicable to forum posts")

    def _get_channels_for_guild(self, guild_id):
        if not guild_id:
            raise Exception("Missing guild_id")
        try:
            response = requests.get(
                f"{DISCORD_BASE_API_URL}/guilds/{guild_id}/channels",
                headers=self._headers,
                timeout=5,
            )
            channels = json.loads(response.content.decode("utf-8"))
            return channels
        except Exception as e:
            print(f"Error getting channels from discord: {e}")

    def _create_channel_invite(self, channel_id, max_age=0):
        raise NotImplementedError("Not needed for forum posts")

    def create_channel_url(self, guild_id, channel_id, is_audio=False):
        if not guild_id or not channel_id:
            raise Exception("Missing guild_id or channel_id")
        return f"https://discord.com/channels/{guild_id}/{channel_id}"

    def handle_tag_added(self, puzzle_announcements_id, puzzle, tag_name):
        from chat.models import ChatRole

        role = ChatRole.objects.filter(name__iexact=tag_name, hunt=puzzle.hunt).first()
        if role is not None:
            self.announce(
                puzzle_announcements_id,
                f"{puzzle.name} was tagged with <@&{role.role_id}>",
                puzzle.create_field_url_map(),
            )
        return

    def handle_tag_removed(self, puzzle_announcements_id, puzzle, tag_name):
        pass  # No specific logic needed here

    def handle_puzzle_rename(self, channel_id, new_name):
        self.edit_forum_post_name(channel_id, new_name)

    def get_all_roles(self, guild_id):
        try:
            response = requests.get(
                f"{DISCORD_BASE_API_URL}/guilds/{guild_id}/roles",
                headers=self._headers,
                timeout=5,
            )
            return json.loads(response.content.decode("utf-8"))
        except Exception as e:
            print(f"Error getting roles from Discord: {e}")

    def create_role(self, guild_id, role_name, color):
        try:
            response = requests.post(
                f"{DISCORD_BASE_API_URL}/guilds/{guild_id}/roles",
                headers=self._headers,
                json={
                    "name": role_name,
                    "color": color,
                    "mentionable": True,
                },
                timeout=5,
            )
            return json.loads(response.content.decode("utf-8"))
        except Exception as e:
            print(f"Error creating Discord role: {e}")

    def get_guild_id(self, puzzle):
        return puzzle.hunt.settings.discord_guild_id