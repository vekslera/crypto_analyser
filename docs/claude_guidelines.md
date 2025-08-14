# Vibe Coding Guidelines
### Here are several points your LLM should be prompted at the start of a vibe coding session. 
### They can help shorten the Code-Refactor-Test-Debug cycle. 

1. You are a prominent coder! Make the strongest effort to help me do my job the best way.
2. Avoid using Unicode-specific characters. They can cause runtime errors. Use ASCII characters only.
3. Strictly avoid hardcoding. Keep all the parameters in config file(s). 
4. While generating code, stick to the SOLID principles. The most important ones are Single Responsibility, Dependency Inversion and Interface Segregation principles. 
5. Attempt to write short functions and classes. Avoid lengthy functions, even if they obey SRP. 
6. Use clear file structure. Group files in folders by their purpose. 
7. Generate a test file for each feature you add, fix or rewrite. Do not delete them after use. Instead, keep them in a file structure similar to the structure of the project, under *tests/* directory.
8. Each major feature development starts with opening a new Git branch. The code should be staged, committed and pushed several times, through the development process. 
9. Once the feature is up and running, and upon my approval, merge the branch into main/master and push. Take care of the DB if it needs separate handling at merge.
10. 
11. Everything important to a user, or a developer, should be updated in README.md or a dedicated help file.

## Thank you very much for your assistance!