"""
Google NLP Content Classification Taxonomy
Common categories for the searchable dropdown.
Full taxonomy: https://cloud.google.com/natural-language/docs/categories
"""

# Most common top-level categories
TOP_LEVEL_CATEGORIES = [
    "/Arts & Entertainment",
    "/Autos & Vehicles",
    "/Beauty & Fitness",
    "/Books & Literature",
    "/Business & Industrial",
    "/Computers & Electronics",
    "/Finance",
    "/Food & Drink",
    "/Games",
    "/Health",
    "/Hobbies & Leisure",
    "/Home & Garden",
    "/Internet & Telecom",
    "/Jobs & Education",
    "/Law & Government",
    "/News",
    "/Online Communities",
    "/People & Society",
    "/Pets & Animals",
    "/Real Estate",
    "/Reference",
    "/Science",
    "/Shopping",
    "/Sports",
    "/Travel"
]

# Travel subcategories (commonly used)
TRAVEL_CATEGORIES = [
    "/Travel",
    "/Travel/Air Travel",
    "/Travel/Bed & Breakfasts",
    "/Travel/Bus & Rail",
    "/Travel/Camping",
    "/Travel/Car Rental & Taxi Services",
    "/Travel/Cruises & Charters",
    "/Travel/Hotels & Accommodations",
    "/Travel/Luggage & Travel Accessories",
    "/Travel/Rail Travel",
    "/Travel/Rental Cars",
    "/Travel/Road Travel",
    "/Travel/Specialty Travel",
    "/Travel/Specialty Travel/Ecotourism",
    "/Travel/Theme Parks",
    "/Travel/Tourist Destinations",
    "/Travel/Tourist Destinations/Beaches & Islands",
    "/Travel/Tourist Destinations/Mountain & Ski Resorts",
    "/Travel/Tourist Destinations/Regional Parks & Gardens",
    "/Travel/Tourist Destinations/Theme Parks",
    "/Travel/Travel Agencies & Services",
    "/Travel/Travel Guides & Travelogues",
    "/Travel/Transports"
]

# Business & Industrial subcategories
BUSINESS_CATEGORIES = [
    "/Business & Industrial",
    "/Business & Industrial/Advertising & Marketing",
    "/Business & Industrial/Business Services",
    "/Business & Industrial/Hospitality Industry"
]

# All categories combined
ALL_CATEGORIES = sorted(list(set(
    TOP_LEVEL_CATEGORIES +
    TRAVEL_CATEGORIES +
    BUSINESS_CATEGORIES
)))
