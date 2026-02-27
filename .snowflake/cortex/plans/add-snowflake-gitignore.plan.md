# Plan: Add .snowflake/ to .gitignore

## Current State
The [.gitignore](.gitignore) currently has `.snowflake/*` on line 66, which ignores files inside the directory but not the directory pattern itself.

## Change
Update line 66 from:
```
.snowflake/*
```
to:
```
.snowflake/
```

This properly ignores the entire `.snowflake/` directory using standard gitignore syntax.