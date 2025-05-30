# Wordbender
An LLM-powered targeted wordlist generator script

## Dev tools
### Run all
```
uv run isort . && uv run black . && uv run flake8 .
```

### black (formatting)
```
uv run black .
```

### isort (import sorting)
```
uv run isort .
```

### flake8
```
uv run flake8 .
```


# TEMP
# First run - setup wizard
python wordbender.py config --setup

# Interactive mode (default)
python wordbender.py

# Direct generation
python wordbender.py generate password -s john -s smith -s 1985 -l 200

# Batch processing
echo -e "apple\nmicrosoft\ngoogle" > companies.txt
python wordbender.py batch companies.txt subdomain

# Check configuration
python wordbender.py config --show
