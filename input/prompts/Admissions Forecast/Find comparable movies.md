---
description: "Comparable movies for: The Super Mario Galaxy Movie"
model: openai/gpt-4o
temperature: 0.7
system: "You are a film domain expert specialized in comparative movie analysis and film release history.

  Your task is to identify movies that are highly comparable to a given TargetMovie, based on provided metadata and weighted similarity criteria.

You must adhere to the following rules:

Selection constraints:
  - Select exactly 10 comparable movies
  - Movies must have been released within the last 10 years
  - Movies must have been released in the specified release country
  - Movies must have been released at least 6 months ago

Similarity evaluation:
  - You will be provided with one or more “Additional Context Sections”
  - Each section defines a similarity topic and an associated weight
  - When determining similarity, consider all sections and their relative weights
  - Higher-weight sections must have greater influence on similarity ranking

Scoring and ranking:
  - Assign a similarity_score between 0 and 10
  - 10 indicates an extremely strong similarity to the TargetMovie
  - 0 indicates no meaningful similarity
  - Rank movies by similarity_score in descending order
  - If two movies have similar similarity scores, prefer the movie with a release date closer to the TargetMovie’s release date

Output requirements:
  - The response must strictly conform to the provided JSON schema
  - All required fields must be present for every movie
  - Do not add any additional fields
  - Do not include explanatory text outside the structured response

Data quality requirements:
  - Each movie must include a valid IMDb URL pointing to the most likely official IMDb entry
  - If exact data is uncertain, choose the most plausible and widely accepted value"
---

# TargetMovie details:

* Title: "The Super Mario Galaxy Movie"
* Release date: 2026-04-01 in Belgium
* IMDB URL: https://www.imdb.com/title/tt28650488
* Directors: Aaron Horvath, Michael Jelenic, Pierre Leduc
* Principal cast: Brie Larson, Chris Pratt, Anya Taylor-Joy, Charlie Day, Benny Safdie, Sebastian Maniscalco, Jessica
  Dicicco and Charles Martinet
* Production countries: France, Japan and United States
* Genres: adventure, comedy, family, animation, fantasy, all
* Rating: 6+

## Additional Context Sections

### Synopsis Paragraph

- Similarity weight: 100
- Similarity field: Consider narrative structure, plot elements, character arcs, thematic focus, tone, genre
  conventions, and the overall setting of the movie.

The Super Mario Galaxy Movie is a 2026 animated adventure comedy film based on the 2007 video game Super Mario Galaxy
and its 2010 sequel, as well as Nintendo's broader Mario franchise. The sequel to The Super Mario Bros. Movie (2023), it
was directed by Aaron Horvath and Michael Jelenic and written by Matthew Fogel. Chris Pratt, Anya Taylor-Joy, Charlie
Day, Jack Black and Keegan-Michael Key reprise their roles, with Benny Safdie, Donald Glover, and Brie Larson joining
the cast. It is produced by Illumination and Nintendo. In the film, Mario and Luigi and their friends adventure into
outer space, where they meet Princess Rosalina and face off against Bowser and his son, Bowser Jr.

Nintendo's president Shuntaro Furukawa stated in May 2021 that Nintendo was interested in producing more animated films
based on its properties if the then-untitled Mario film was successful. Illumination CEO and producer Chris Meledandri
was asked about the possibility of a sequel to The Super Mario Bros. Movie before the film's release in April 2023.
Following its box office success, a new animated Mario film was announced to be in development at Illumination in March
2024, with Horvath and Jelenic returning as directors and Fogel as screenwriter.

The Super Mario Galaxy Movie premiered at Minami-za in Kyoto on March 28, 2026, and was theatrically released in the
United States on April 1 by Universal Pictures. It received negative reviews from critics and
grossed $129.4 million worldwide against a $110 million budget.

### Marketing Paragraph

- Similarity weight: 80
- Similarity field: Consider marketing strategy and campaign style. Prioritize movies with comparable marketing
  approaches.

The Super Mario Galaxy Movie is a 2026 animated adventure comedy film based on the 2007 video game Super Mario Galaxy
and its 2010 sequel, as well as Nintendo's broader Mario franchise. The sequel to The Super Mario Bros. Movie (2023), it
was directed by Aaron Horvath and Michael Jelenic and written by Matthew Fogel. Chris Pratt, Anya Taylor-Joy, Charlie
Day, Jack Black and Keegan-Michael Key reprise their roles, with Benny Safdie, Donald Glover, and Brie Larson joining
the cast. It is produced by Illumination and Nintendo. In the film, Mario and Luigi and their friends adventure into
outer space, where they meet Princess Rosalina and face off against Bowser and his son, Bowser Jr.
Nintendo's president Shuntaro Furukawa stated in May 2021 that Nintendo was interested in producing more animated films
based on its properties if the then-untitled Mario film was successful. Illumination CEO and producer Chris Meledandri
was asked about the possibility of a sequel to The Super Mario Bros. Movie before the film's release in April 2023.
Following its box office success, a new animated Mario film was announced to be in development at Illumination in March
2024, with Horvath and Jelenic returning as directors and Fogel as screenwriter.
The Super Mario Galaxy Movie premiered at Minami-za in Kyoto on March 28, 2026, and was theatrically released in the
United States on April 1 by Universal Pictures. It received negative reviews from critics and
grossed $129.4 million worldwide against a $110 million budget.

Use the above information to identify exactly 10 comparable movies.
Explain in the `remarks` field how the similarity criteria influenced your selection for each movie.
Ensure the response strictly follows the required JSON schema.
