# vertex2tabby

A simply proxy allowing you to use generative AI models hosted on Google Cloud
([Vertex AI](https://docs.cloud.google.com/vertex-ai/docs/start/introduction-unified-platform))
together with [Tabby](https://www.tabbyml.com/).

## How it works

It's an HTTP server running locally that listens on localhost, uses your Google
Cloud [Application Default Credentials (ADC)](https://docs.cloud.google.com/docs/authentication/application-default-credentials)
to get an access token, then calls a Vertex AI endpoint and transforms the
results.

### Supported conversions

- [`openai/chat`](https://tabby.tabbyml.com/docs/references/models-http-api/deepseek/) ⇒ [DeepSeek-V3.2](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/maas/deepseek/deepseek-v32)
- [`mistral/chat`](https://tabby.tabbyml.com/docs/references/models-http-api/mistral-ai/) ⇒ [Codestral 2](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/partner-models/mistral/codestral-2)
- [`mistral/completion`](https://tabby.tabbyml.com/docs/references/models-http-api/mistral-ai/) ⇒ [Codestral 2](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/partner-models/mistral/codestral-2)
- [`azure/embedding`](https://tabby.tabbyml.com/docs/references/models-http-api/azure-openai/) ⇒ [Text embeddings API](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/text-embeddings-api)

## How to use

### Set up Tabby

First, download and install Tabby.

You can use the CPU-only version for [Linux](https://tabby.tabbyml.com/docs/quick-start/installation/linux/),
[Windows](https://tabby.tabbyml.com/docs/quick-start/installation/windows/) or
[Apple](https://tabby.tabbyml.com/docs/quick-start/installation/apple/) if you
don't need any local models.

Then, create `config.toml` in `$HOME/.tabby` on Linux or MacOS or
`%USERPROFILE%\.tabby` on Windows with the following contents:

```
[model.completion.http]
kind = "mistral/completion"
model_name = "codestral-2"
api_endpoint = "http://localhost:4000"
api_key = ""

[model.embedding.http]
kind = "azure/embedding"
model_name = "text-embedding"
api_endpoint = "http://localhost:4000"
api_key = ""

[model.chat.http]
kind = "openai/chat"
model_name = "deepseek-v3.2-maas"
api_endpoint = "http://localhost:4000"
api_key = ""
```

If you'd like to use Codestral 2 instead of DeepSeek for your chat, replace the
`model.chat.http` entry with this:

```
[model.chat.http]
kind = "mistral/chat"
model_name = "codestral-2"
api_endpoint = "http://localhost:4000"
api_key = ""
```

### Enable the models

Depending on your needs, you'll need to enable one or more of these models in
your cloud project:

- [Codestral 2](https://console.cloud.google.com/vertex-ai/publishers/mistralai/model-garden/codestral-2)
- [DeepSeek V3.2 API Service](https://console.cloud.google.com/vertex-ai/publishers/deepseek-ai/model-garden/deepseek-v3.2-maas)
- [Embeddings for Text](https://console.cloud.google.com/vertex-ai/publishers/google/model-garden/textembedding-gecko)

### Start the proxy

First, [install Pixi](https://pixi.prefix.dev/latest/installation/) and the
[`gcloud` CLI](https://docs.cloud.google.com/sdk/docs/install-sdk).

Then, initialize your ADC for Google Cloud and set the environment variables:

```bash
gcloud auth application-default login

export GOOGLE_PROJECT_ID="your-cloud-project-id"
export GOOGLE_REGION="europe-west4" # or "us-central1", only used by Codestral 2
```

Finally, start the proxy:

```bash
pixi run start
```

Then start Tabby and go to http://localhost:8080/system to verify the models
work.

## Docker

To make things easier, you can use the provided docker image which already
includes Tabby with the proxy.

First, follow the steps above to install `gcloud` and generate a token.

```
gcloud auth application-default login

mkdir secrets
cp "$HOME/.config/gcloud/application_default_credentials.json" "./secrets/google_adc.json"
```

Then, start docker. In this example, Tabby will be accessible on
http://localhost:11000/

```
docker run \
  --env GOOGLE_PROJECT_ID=your-cloud-project-id \
  --env GOOGLE_REGION=europe-west4 \
  --mount source=./secrets,destination=/run/secrets,type=bind \
  --mount source=./data,destination=/root/.tabby,type=bind \
  -p 11000:8080 \
  ghcr.io/fstanis/vertex2tabby/vertex2tabby
```
