FROM eclipse-temurin:21-jdk AS build
WORKDIR /app
COPY . .
RUN chmod +x mvnw && ./mvnw -q -DskipTests package

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /app/target/ecommerce-cs-skill-1.0.0-SNAPSHOT.jar app.jar
ENV PORT=8080 \
    LLM_BASE_URL=http://host.docker.internal:11434/v1 \
    LLM_API_KEY=local \
    LLM_MODEL=qwen2.5:7b
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar", "--serve"]
