from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Sequence, Tuple, Union

from fb_outreach.agent import PitchService, UserData
from fb_outreach.prospect_builder import build_prospects
from fb_outreach.schemas import ProspectContext


ProspectBuilderOutput = Union[
    List[ProspectContext],
    Tuple[List[ProspectContext], List[Dict[str, Any]]],
]
ProspectBuilder = Callable[[str], ProspectBuilderOutput]
PersistPitchFn = Callable[[ProspectContext, str], Awaitable[None]]
UserDataFactory = Callable[[ProspectContext], UserData]


@dataclass
class PitchGenerationResultItem:
    page_id: str
    page_name: str
    email: str
    status: str
    pitch: str = ""
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_id": self.page_id,
            "page_name": self.page_name,
            "email": self.email,
            "status": self.status,
            "pitch": self.pitch,
            "error": self.error,
        }


@dataclass
class PitchGenerationResponse:
    generated_count: int
    skipped_missing_email: int
    failed: int
    results: List[PitchGenerationResultItem]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_count": self.generated_count,
            "skipped_missing_email": self.skipped_missing_email,
            "failed": self.failed,
            "results": [item.to_dict() for item in self.results],
        }


class PitchGenerationService:
    """
    Application-layer orchestration service for pitch generation.

    Responsibilities:
    - Build prospects from existing domain logic (ProspectBuilder)
    - Generate pitches via injected PitchService
    - Optionally persist generated pitches via injected callback
    - Return a structured, route-friendly response payload
    """

    def __init__(
        self,
        *,
        pitch_service: PitchService,
        prospect_builder: ProspectBuilder = build_prospects,
        user_data_factory: UserDataFactory | None = None,
        persist_pitch: PersistPitchFn | None = None,
        max_concurrency: int = 3,
    ):
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")

        self._pitch_service = pitch_service
        self._prospect_builder = prospect_builder
        self._user_data_factory = user_data_factory or self._default_user_data_factory
        self._persist_pitch = persist_pitch
        self._max_concurrency = max_concurrency

    async def generate(
        self,
        *,
        user_input: str,
        user_id: str | None = None,
        prospects: Sequence[ProspectContext] | None = None,
    ) -> Dict[str, Any]:
        """
        Generate pitches for prospects.

        Input modes:
        - user_id: uses injected ProspectBuilder to load prospects
        - prospects: directly accepts already-built prospects

        Exactly one of `user_id` or `prospects` must be provided.
      0  """
        if bool(user_id) == bool(prospects):
            raise ValueError("Provide exactly one of user_id or prospects")

        skipped_missing_email = 0
        results: List[PitchGenerationResultItem] = []

        if user_id:
            raw_output = self._prospect_builder(user_id)
            candidate_prospects, missing_email_items = self._normalize_builder_output(raw_output)
            skipped_missing_email = len(missing_email_items)
            results.extend(
                [
                    PitchGenerationResultItem(
                        page_id=str(item.get("page_id", "")),
                        page_name=str(item.get("page_name", "")),
                        email="",
                        status="skipped",
                        error="missing_or_invalid_email",
                    )
                    for item in missing_email_items
                ]
            )
        else:
            candidate_prospects = list(prospects or [])

        valid_prospects: List[ProspectContext] = []
        for prospect in candidate_prospects:
            if prospect.is_valid_for_outreach():
                valid_prospects.append(prospect)
            else:
                skipped_missing_email += 1
                results.append(
                    PitchGenerationResultItem(
                        page_id=prospect.page_id,
                        page_name=prospect.page_name,
                        email=prospect.email,
                        status="skipped",
                        error="missing_or_invalid_email",
                    )
                )

        if not valid_prospects:
            response = PitchGenerationResponse(
                generated_count=0,
                skipped_missing_email=skipped_missing_email,
                failed=0,
                results=results,
            )
            return response.to_dict()

        semaphore = asyncio.Semaphore(self._max_concurrency)
        tasks = [
            self._generate_single_pitch(
                prospect=prospect,
                user_input=user_input,
                semaphore=semaphore,
            )
            for prospect in valid_prospects
        ]

        generated_items = await asyncio.gather(*tasks)
        results.extend(generated_items)

        generated_count = sum(1 for item in generated_items if item.status == "generated")
        failed = sum(1 for item in generated_items if item.status == "failed")

        response = PitchGenerationResponse(
            generated_count=generated_count,
            skipped_missing_email=skipped_missing_email,
            failed=failed,
            results=results,
        )
        return response.to_dict()

    async def _generate_single_pitch(
        self,
        *,
        prospect: ProspectContext,
        user_input: str,
        semaphore: asyncio.Semaphore,
    ) -> PitchGenerationResultItem:
        async with semaphore:
            try:
                context = self._user_data_factory(prospect)
                pitch = await self._pitch_service.generate_pitch(
                    user_input=user_input,
                    context=context,
                )

                if self._persist_pitch:
                    await self._persist_pitch(prospect, pitch)

                return PitchGenerationResultItem(
                    page_id=prospect.page_id,
                    page_name=prospect.page_name,
                    email=prospect.email,
                    status="generated",
                    pitch=pitch,
                )
            except Exception as exc:
                return PitchGenerationResultItem(
                    page_id=prospect.page_id,
                    page_name=prospect.page_name,
                    email=prospect.email,
                    status="failed",
                    error=str(exc),
                )

    @staticmethod
    def _default_user_data_factory(prospect: ProspectContext) -> UserData:
        return UserData(
            page_name=prospect.page_name,
            email=prospect.email,
            title=prospect.category,
            company=prospect.company or prospect.page_name,
            business_detail=prospect.business_description or prospect.intro,
            followers=prospect.followers,
            intro=prospect.intro,
            info=prospect.raw_data,
            likes=prospect.likes,
            address=prospect.address,
        )

    @staticmethod
    def _normalize_builder_output(
        output: ProspectBuilderOutput,
    ) -> Tuple[List[ProspectContext], List[Dict[str, Any]]]:
        if isinstance(output, tuple):
            prospects, missing = output
            return list(prospects or []), list(missing or [])

        if isinstance(output, list):
            return list(output), []

        raise TypeError(
            "Prospect builder must return List[ProspectContext] "
            "or Tuple[List[ProspectContext], List[Dict[str, Any]]]."
        )
