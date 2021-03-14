# Home Assistant sensor for german AHE waste collection schedule

## Installation:
### Hacs
Search for ahe in hacs integrations, install and restart home assistant

### Manual
Copy all files from custom_components/ahe/ to custom_components/ahe/ inside your config Home Assistant directory.

```yaml
- platform: ahe
  name: ahe
  scan_interval: 3600
  city: ''
  street: ''
  house_number: ''
  zip: ''
```
