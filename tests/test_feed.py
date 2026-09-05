from datetime import date, timedelta

import pytest

from flauschi_pipeline.feed import Episode, FeedMalformedException, parse_feed

RSS_FEED = """
<rss version="2.0">
	<channel>
		<atom:link href="https://feeds.megaphone.fm/GLT4060321204" rel="self" type="application/rss+xml"/>
		<title>Fest & Flauschig</title>
		<link>http://festundflauschig.de/</link>
		<language>de</language>
		<copyright/>
		<description>
Fest & Flauschig mit Jan Böhmermann und Olli Schulz. Der preisgekrönte, verblüffend fabelhafte, grenzenlos fantastische Podcast für sie, ihn und es.
</description>
		<item>
			<title>Best of 10 Jahre Fest & Flauschig Gäste</title>
			<description>
Die schönsten Gespräche finden manchmal zu dritt statt- für Gäste wird auch mal der Teller mit den abgeschnittenen Fußnägeln weggeräumt und eine Hose angezogen. Bühne frei für die legendärsten Besuche aus 10 Jahren. Mit Bill Kaulitz, Bela B., Palina Rojinski, Detlev Buck, Barbara Schöneberger, Bjarne Mädel, Laura Larsson, Deniz Yücel, Katrin Bauerfeind und Riccardo Simonetti Learn more about your ad choices. Visit podcastchoices.com/adchoices
</description>
			<pubDate>Sat, 29 Aug 2026 21:50:00 -0000</pubDate>
			<itunes:episodeType>full</itunes:episodeType>
			<itunes:author>Jan Böhmermann & Olli Schulz</itunes:author>
			<itunes:subtitle/>
			<itunes:summary>
Die schönsten Gespräche finden manchmal zu dritt statt- für Gäste wird auch mal der Teller mit den abgeschnittenen Fußnägeln weggeräumt und eine Hose angezogen. Bühne frei für die legendärsten Besuche aus 10 Jahren. Mit Bill Kaulitz, Bela B., Palina Rojinski, Detlev Buck, Barbara Schöneberger, Bjarne Mädel, Laura Larsson, Deniz Yücel, Katrin Bauerfeind und Riccardo Simonetti Learn more about your ad choices. Visit podcastchoices.com/adchoices
</itunes:summary>
			<content:encoded>
				<p>Die schönsten Gespräche finden manchmal zu dritt statt- für Gäste wird auch mal der Teller mit den abgeschnittenen Fußnägeln weggeräumt und eine Hose angezogen. Bühne frei für die legendärsten Besuche aus 10 Jahren.</p>
				<p>Mit Bill Kaulitz, Bela B., Palina Rojinski, Detlev Buck, Barbara Schöneberger, Bjarne Mädel, Laura Larsson, Deniz Yücel, Katrin Bauerfeind und Riccardo Simonetti</p>
				<p></p>
				<p>Learn more about your ad choices. Visit
					<a href="https://podcastchoices.com/adchoices">podcastchoices.com/adchoices</a>
				</p>
			</content:encoded>
			<itunes:duration>4565</itunes:duration>
			<guid isPermaLink="false">a956ecd8-a12d-11f1-b06d-ab2773b6143d</guid>
			<enclosure url="https://traffic.megaphone.fm/GLT9301027852.mp3" length="0" type="audio/mpeg"/>
		</item>
		<item>
			<title>Best of 10 Jahre Fest & Flauschig 10/10</title>
			<description>
Erstaunlich, was über die Jahre so passieren kann, vor 10 Jahren wurde dieser Podcast noch mit Dosentelefonen aufgenommen. Und so manche*r Politiker*in hat seinen Hut genommen. Was bleibt, sind Füße, der gute alte Pimmelwitz und ganz ganz große Liebe. Learn more about your ad choices. Visit podcastchoices.com/adchoices
</description>
			<pubDate>Sat, 22 Aug 2026 21:50:00 -0000</pubDate>
			<itunes:episodeType>full</itunes:episodeType>
			<itunes:author>Jan Böhmermann & Olli Schulz</itunes:author>
			<itunes:subtitle/>
			<itunes:summary>
Erstaunlich, was über die Jahre so passieren kann, vor 10 Jahren wurde dieser Podcast noch mit Dosentelefonen aufgenommen. Und so manche*r Politiker*in hat seinen Hut genommen. Was bleibt, sind Füße, der gute alte Pimmelwitz und ganz ganz große Liebe. Learn more about your ad choices. Visit podcastchoices.com/adchoices
</itunes:summary>
			<content:encoded>
				<p>Erstaunlich, was über die Jahre so passieren kann, vor 10 Jahren wurde dieser Podcast noch mit Dosentelefonen aufgenommen. Und so manche*r Politiker*in hat seinen Hut genommen. Was bleibt, sind Füße, der gute alte Pimmelwitz und ganz ganz große Liebe. </p>
				<p></p>
				<p>Learn more about your ad choices. Visit
					<a href="https://podcastchoices.com/adchoices">podcastchoices.com/adchoices</a>
				</p>
			</content:encoded>
			<itunes:duration>5895</itunes:duration>
			<guid isPermaLink="false">ed207b9e-9ccf-11f1-bb52-9bae8780bfb0</guid>
			<enclosure url="https://traffic.megaphone.fm/GLT3495772886.mp3" length="0" type="audio/mpeg"/>
		</item>
	</channel>
</rss>
"""

EMPTY_FEED = """
<rss version="2.0">
	<channel>
		<title>Fest & Flauschig</title>
	</channel>
</rss>
"""

FEED_WITHOUT_ENCLOSURE = """
<rss version="2.0">
	<channel>
		<title>Fest & Flauschig</title>
		<item>
			<title>Ohne Anhang</title>
			<description>Für diese Folge gibt es kein Audio.</description>
			<pubDate>Sat, 01 Aug 2026 21:50:00 -0000</pubDate>
			<itunes:duration>100</itunes:duration>
			<guid isPermaLink="false">no-enclosure</guid>
		</item>
	</channel>
</rss>
"""

VIDEO_ONLY_FEED = """
<rss version="2.0">
	<channel>
		<title>Fest & Flauschig</title>
		<item>
			<title>Nur Video</title>
			<description>Für diese Folge gibt es nur ein Video.</description>
			<pubDate>Sat, 01 Aug 2026 21:50:00 -0000</pubDate>
			<itunes:duration>100</itunes:duration>
			<guid isPermaLink="false">video-only</guid>
			<enclosure url="https://traffic.megaphone.fm/GLT1.mp4" length="0" type="video/mp4"/>
		</item>
	</channel>
</rss>
"""

MIXED_ENCLOSURES_FEED = """
<rss version="2.0">
	<channel>
		<title>Fest & Flauschig</title>
		<item>
			<title>Mit Video und Audio</title>
			<description>Für diese Folge gibt es ein Video und ein Audio.</description>
			<pubDate>Sat, 01 Aug 2026 21:50:00 -0000</pubDate>
			<itunes:duration>100</itunes:duration>
			<guid isPermaLink="false">mixed</guid>
			<enclosure url="https://traffic.megaphone.fm/GLT1.mp4" length="0" type="video/mp4"/>
			<enclosure url="https://traffic.megaphone.fm/GLT1234567890.mp3" length="0" type="audio/mpeg"/>
		</item>
	</channel>
</rss>
"""

EXPECTED_NEWEST_EPISODE = Episode(
	id="a956ecd8-a12d-11f1-b06d-ab2773b6143d",
	publication_date=date(2026, 8, 29),
	title="Best of 10 Jahre Fest & Flauschig Gäste",
	description="Die schönsten Gespräche finden manchmal zu dritt statt- für Gäste wird auch mal der Teller mit den abgeschnittenen Fußnägeln weggeräumt und eine Hose angezogen. Bühne frei für die legendärsten Besuche aus 10 Jahren. Mit Bill Kaulitz, Bela B., Palina Rojinski, Detlev Buck, Barbara Schöneberger, Bjarne Mädel, Laura Larsson, Deniz Yücel, Katrin Bauerfeind und Riccardo Simonetti Learn more about your ad choices. Visit podcastchoices.com/adchoices",
	audio_url="https://traffic.megaphone.fm/GLT9301027852.mp3",
	duration=timedelta(seconds=4565),
)


def test_parse_feed_parses_episode_fields() -> None:
    episodes, _ = parse_feed(RSS_FEED, last_modified=None)
    assert episodes[0] == EXPECTED_NEWEST_EPISODE


def test_parse_feed_sorts_episodes_newest_first() -> None:
    episodes, _ = parse_feed(RSS_FEED, last_modified=None)
    assert [episode.publication_date for episode in episodes] == [
        date(2026, 8, 29),
        date(2026, 8, 22),
    ]
    assert [episode.id for episode in episodes] == [
        "a956ecd8-a12d-11f1-b06d-ab2773b6143d",
        "ed207b9e-9ccf-11f1-bb52-9bae8780bfb0",
    ]


def test_parse_feed_parses_older_episode() -> None:
    episodes, _ = parse_feed(RSS_FEED, last_modified=None)
    older = episodes[1]
    assert older.title == "Best of 10 Jahre Fest & Flauschig 10/10"
    assert older.duration == timedelta(seconds=5895)
    assert older.audio_url == "https://traffic.megaphone.fm/GLT3495772886.mp3"


def test_parse_feed_returns_no_modified_date_for_documents() -> None:
    _, modified = parse_feed(RSS_FEED, last_modified=None)
    assert modified is None


def test_parse_feed_with_empty_channel() -> None:
    episodes, modified = parse_feed(EMPTY_FEED, last_modified=None)
    assert episodes == []
    assert modified is None


def test_parse_feed_without_enclosure_raises() -> None:
    with pytest.raises(FeedMalformedException, match="No audio file present"):
        parse_feed(FEED_WITHOUT_ENCLOSURE, last_modified=None)


def test_parse_feed_with_non_audio_enclosure_raises() -> None:
    with pytest.raises(FeedMalformedException, match="No audio file present"):
        parse_feed(VIDEO_ONLY_FEED, last_modified=None)


def test_parse_feed_selects_audio_enclosure() -> None:
    episodes, _ = parse_feed(MIXED_ENCLOSURES_FEED, last_modified=None)
    assert episodes[0].audio_url == "https://traffic.megaphone.fm/GLT1234567890.mp3"


def test_episode_slug_combines_date_and_title() -> None:
    episode = Episode(
        id="test-id",
        publication_date=date(2026, 8, 29),
        title="Best of 10 Jahre Fest & Flauschig Gäste",
        description="Test description",
        audio_url="https://traffic.megaphone.fm/test.mp3",
        duration=timedelta(seconds=4565),
    )
    assert episode.slug == "2026-08-29-best-of-10-jahre-fest-flauschig-gaeste"
