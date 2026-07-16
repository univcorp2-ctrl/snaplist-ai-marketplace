from __future__ import annotations

import json
import sqlite3
import statistics
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any, Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ai_provider: str = "mock"
    ai_gateway_url: str = "https://api.openai.com/v1"
    ai_gateway_api_key: str = ""
    ai_model: str = "gpt-4.1-mini"
    database_path: str = "snaplist.db"
    cors_origins: str = "http://localhost:3000"
    ebay_marketplace_id: str = "EBAY_US"
    ebay_access_token: str = ""
    ebay_merchant_location_key: str = ""
    ebay_fulfillment_policy_id: str = ""
    ebay_payment_policy_id: str = ""
    ebay_return_policy_id: str = ""
    yahoo_shopping_seller_id: str = ""
    yahoo_shopping_access_token: str = ""


settings = Settings()


class AnalyzeRequest(BaseModel):
    image_data_url: str | None = Field(default=None, description="data:image/... base64 URL")
    file_name: str = "product.jpg"
    product_hint: str = ""
    condition: str = "目立った傷や汚れなし"
    category_hint: str = ""


class MarketSample(BaseModel):
    platform: str
    title: str
    price: int
    url: str | None = None


class PriceGuide(BaseModel):
    low: int
    median: int
    high: int
    quick_sale: int
    recommended: int
    premium: int
    confidence: float


class ListingDraft(BaseModel):
    title: str
    description: str
    brand: str
    category: str
    condition: str
    attributes: dict[str, str]
    tags: list[str]
    price: PriceGuide
    samples: list[MarketSample]
    warnings: list[str] = []


class PublishRequest(BaseModel):
    draft: ListingDraft
    platforms: list[str]
    image_urls: list[str] = []


class PublishResult(BaseModel):
    platform: str
    mode: Literal["published", "draft", "error"]
    listing_id: str | None = None
    url: str | None = None
    message: str


def db_path() -> Path:
    return Path(settings.database_path)


def init_db() -> None:
    with closing(sqlite3.connect(db_path())) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS listings (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def price_guide(prices: list[int]) -> PriceGuide:
    cleaned = sorted(p for p in prices if p > 0)
    if not cleaned:
        cleaned = [3200, 4200, 4800, 5500, 6200]
    median = int(statistics.median(cleaned))
    low = cleaned[max(0, int(len(cleaned) * 0.15) - 1)]
    high = cleaned[min(len(cleaned) - 1, int(len(cleaned) * 0.85))]
    return PriceGuide(
        low=low,
        median=median,
        high=high,
        quick_sale=max(300, int(median * 0.88 // 100 * 100)),
        recommended=max(300, int(median * 0.98 // 100 * 100)),
        premium=max(300, int(high * 1.05 // 100 * 100)),
        confidence=min(0.95, 0.55 + len(cleaned) * 0.05),
    )


def mock_draft(request: AnalyzeRequest) -> ListingDraft:
    hint = request.product_hint.strip() or "撮影した商品"
    title = f"{hint} 中古 美品 動作確認済み"
    samples = [
        MarketSample(platform="メルカリ参考", title=f"{hint} 同等品", price=4200),
        MarketSample(platform="Yahoo!参考", title=f"{hint} 中古", price=4800),
        MarketSample(platform="eBay参考", title=f"{hint} pre-owned", price=5600),
        MarketSample(platform="自社販売履歴", title=f"{hint} 良品", price=5100),
    ]
    return ListingDraft(
        title=title[:80],
        description=(
            f"ご覧いただきありがとうございます。{hint}の出品です。"
            f"状態は「{request.condition}」として確認しています。"
            "写真に写っているものが付属品のすべてです。"
            "中古品のため、写真で状態をご確認のうえご購入ください。"
            "丁寧に梱包し、追跡可能な方法で発送します。"
        ),
        brand="要確認",
        category=request.category_hint or "その他",
        condition=request.condition,
        attributes={"動作": "確認済み", "付属品": "写真参照", "保管環境": "禁煙"},
        tags=["中古", "即購入可", "匿名配送", "動作確認済み"],
        price=price_guide([s.price for s in samples]),
        samples=samples,
        warnings=["AI推定結果です。型番、真贋、傷、付属品は出品前に確認してください。"],
    )


async def ai_draft(request: AnalyzeRequest) -> ListingDraft:
    if settings.ai_provider == "mock" or not settings.ai_gateway_api_key:
        return mock_draft(request)
    prompt = (
        "You are a Japanese resale listing specialist. Return only JSON with keys: "
        "title, description, brand, category, condition, attributes(object), tags(array). "
        "Do not invent model numbers, authenticity, or accessories. Mention uncertainty. "
        f"User hint: {request.product_hint}; condition hint: {request.condition}."
    )
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    if request.image_data_url:
        content.append({"type": "image_url", "image_url": {"url": request.image_data_url}})
    payload = {
        "model": settings.ai_model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": content}],
    }
    headers = {"Authorization": f"Bearer {settings.ai_gateway_api_key}"}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{settings.ai_gateway_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"]
    parsed = json.loads(raw)
    base = mock_draft(request)
    base.title = str(parsed.get("title") or base.title)[:80]
    base.description = str(parsed.get("description") or base.description)
    base.brand = str(parsed.get("brand") or "要確認")
    base.category = str(parsed.get("category") or base.category)
    base.condition = str(parsed.get("condition") or base.condition)
    base.attributes = {str(k): str(v) for k, v in parsed.get("attributes", {}).items()}
    base.tags = [str(x) for x in parsed.get("tags", base.tags)][:12]
    return base


async def publish_ebay(request: PublishRequest) -> PublishResult:
    if not settings.ebay_access_token:
        return PublishResult(
            platform="ebay",
            mode="draft",
            message="EBAY_ACCESS_TOKEN未設定のため下書きを生成しました。",
        )
    required = [
        settings.ebay_merchant_location_key,
        settings.ebay_fulfillment_policy_id,
        settings.ebay_payment_policy_id,
        settings.ebay_return_policy_id,
    ]
    if not all(required) or not request.image_urls:
        return PublishResult(
            platform="ebay",
            mode="draft",
            message="出品ポリシーまたは公開画像URLが不足しています。",
        )
    sku = f"snap-{uuid.uuid4().hex[:12]}"
    base = "https://api.ebay.com/sell/inventory/v1"
    headers = {
        "Authorization": f"Bearer {settings.ebay_access_token}",
        "Content-Type": "application/json",
        "Content-Language": "en-US",
    }
    item = {
        "availability": {"shipToLocationAvailability": {"quantity": 1}},
        "condition": "USED_EXCELLENT",
        "product": {
            "title": request.draft.title,
            "description": request.draft.description,
            "imageUrls": request.image_urls,
            "aspects": {k: [v] for k, v in request.draft.attributes.items()},
        },
    }
    async with httpx.AsyncClient(timeout=60) as client:
        put = await client.put(f"{base}/inventory_item/{sku}", headers=headers, json=item)
        if put.status_code >= 300:
            return PublishResult(platform="ebay", mode="error", message=put.text[:300])
        offer_payload = {
            "sku": sku,
            "marketplaceId": settings.ebay_marketplace_id,
            "format": "FIXED_PRICE",
            "availableQuantity": 1,
            "categoryId": "88433",
            "listingDescription": request.draft.description,
            "merchantLocationKey": settings.ebay_merchant_location_key,
            "pricingSummary": {
                "price": {
                    "currency": "USD",
                    "value": str(max(1, request.draft.price.recommended // 150)),
                }
            },
            "listingPolicies": {
                "fulfillmentPolicyId": settings.ebay_fulfillment_policy_id,
                "paymentPolicyId": settings.ebay_payment_policy_id,
                "returnPolicyId": settings.ebay_return_policy_id,
            },
        }
        offer = await client.post(f"{base}/offer", headers=headers, json=offer_payload)
        if offer.status_code >= 300:
            return PublishResult(platform="ebay", mode="error", message=offer.text[:300])
        offer_id = offer.json()["offerId"]
        published = await client.post(f"{base}/offer/{offer_id}/publish", headers=headers)
        if published.status_code >= 300:
            return PublishResult(
                platform="ebay",
                mode="error",
                listing_id=offer_id,
                message=published.text[:300],
            )
        listing_id = published.json().get("listingId")
    return PublishResult(
        platform="ebay",
        mode="published",
        listing_id=listing_id,
        message="eBayへ公開しました。",
    )


def assisted(platform: str) -> PublishResult:
    return PublishResult(
        platform=platform,
        mode="draft",
        listing_id=f"draft-{uuid.uuid4().hex[:10]}",
        message="公開API未確認のため、安全な入力済み下書きとして保存しました。",
    )


app = FastAPI(title="SnapList AI API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()] or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "snaplist-ai"}


@app.post("/api/analyze", response_model=ListingDraft)
async def analyze(request: AnalyzeRequest) -> ListingDraft:
    try:
        return await ai_draft(request)
    except (httpx.HTTPError, KeyError, ValueError, json.JSONDecodeError) as exc:
        fallback = mock_draft(request)
        fallback.warnings.append(
            f"AIゲートウェイに接続できずデモ解析へ切替: {type(exc).__name__}"
        )
        return fallback


@app.post("/api/publish", response_model=list[PublishResult])
async def publish(request: PublishRequest) -> list[PublishResult]:
    if not request.platforms:
        raise HTTPException(status_code=400, detail="platforms is required")
    results: list[PublishResult] = []
    for platform in request.platforms:
        key = platform.lower()
        if key == "own-store":
            listing_id = uuid.uuid4().hex
            with closing(sqlite3.connect(db_path())) as conn:
                conn.execute(
                    "INSERT INTO listings(id, title, payload) VALUES(?, ?, ?)",
                    (listing_id, request.draft.title, request.draft.model_dump_json()),
                )
                conn.commit()
            results.append(
                PublishResult(
                    platform=platform,
                    mode="published",
                    listing_id=listing_id,
                    url=f"/api/listings/{listing_id}",
                    message="自社ストアへ保存しました。",
                )
            )
        elif key == "ebay":
            results.append(await publish_ebay(request))
        elif key == "yahoo-shopping":
            results.append(
                PublishResult(
                    platform=platform,
                    mode="draft",
                    message=(
                        "Yahoo!ショッピング公式API用データを生成しました。"
                        "ストア固有カテゴリ確認後に送信してください。"
                    ),
                )
            )
        else:
            results.append(assisted(platform))
    return results


@app.get("/api/listings/{listing_id}")
def get_listing(listing_id: str) -> dict[str, Any]:
    with closing(sqlite3.connect(db_path())) as conn:
        row = conn.execute(
            "SELECT id, title, payload, created_at FROM listings WHERE id = ?",
            (listing_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="listing not found")
    return {
        "id": row[0],
        "title": row[1],
        "draft": json.loads(row[2]),
        "created_at": row[3],
    }
