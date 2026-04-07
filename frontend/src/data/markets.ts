export interface Market {
  code: string;
  state: string;
  label: string;
  zip: string;
  city: string;
}

export const MARKETS: Market[] = [
  { code: "US-CA", state: "CA", label: "California", zip: "90210", city: "Beverly Hills" },
  { code: "US-TX", state: "TX", label: "Texas", zip: "75201", city: "Dallas" },
  { code: "US-CO", state: "CO", label: "Colorado", zip: "80202", city: "Denver" },
  { code: "US-UT", state: "UT", label: "Utah", zip: "84101", city: "Salt Lake City" },
  { code: "US-MA", state: "MA", label: "Massachusetts", zip: "02101", city: "Boston" },
  { code: "US-NY", state: "NY", label: "New York", zip: "10001", city: "New York" },
  { code: "US-HI", state: "HI", label: "Hawaii", zip: "96801", city: "Honolulu" },
  { code: "US-KY", state: "KY", label: "Kentucky", zip: "40202", city: "Louisville" },
];
