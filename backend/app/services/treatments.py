"""Conservative educational guidance for model outputs; not a pesticide prescription."""


def general_guidance(label: str | None, analysis_type: str = "disease") -> dict:
    task_name = "pest" if analysis_type == "pest" else "disease"
    if not label:
        model_name = "pest" if task_name == "pest" else "disease"
        return {
            "title": f"{model_name.title()} model not ready",
            "summary": f"The image was saved, but no validated {model_name} prediction was available.",
            "actions": [
                "Train the matching classifier and install its model and class-label files before expecting predictions.",
                "For a crop-threatening or spreading problem, consult a qualified local agronomist or plant pathologist.",
            ],
            "safety_note": "No diagnosis or product prescription has been generated.",
        }

    readable_label = label.replace("___", " — ").replace("_", " ").strip()
    lowered = label.lower()
    if task_name == "pest":
        if "healthy" in lowered or "no_pest" in lowered:
            summary = "The model's closest labelled category suggests no target pest was identified. This does not rule out all pests."
            actions = ["Inspect the undersides of leaves and growing tips during routine monitoring.", "Protect beneficial insects and avoid spraying unless a specific pest is confirmed."]
        else:
            summary = "The image resembles a labelled pest category. Confirm the insect and the level of crop damage before choosing a control."
            actions = [
                "Inspect several plants and check the underside of leaves for eggs, nymphs, webbing or feeding damage.",
                "Where practical, start with monitoring and physical removal; protect pollinators and natural enemies.",
                "If a botanical or soap product is considered, check its local label, test a small area first and avoid spraying flowering plants or active pollinators.",
                "Ask an agricultural extension officer or agronomist to confirm the pest if crop damage is spreading.",
            ]
    elif "healthy" in lowered:
        summary = "The model's closest class is a healthy category. This does not rule out every plant problem."
        actions = ["Continue routine monitoring and compare new photos over time.", "Avoid applying pesticide or fertilizer without a specific need supported by observations or lab results.", "Keep irrigation and nutrition suitable for the crop and growth stage."]
    elif any(term in lowered for term in ("virus", "mosaic")):
        summary = "The image resembles a labelled virus-related category. Visual classification alone cannot confirm a viral infection."
        actions = ["Separate the affected plant from routine handling where practical and clean tools between plants.", "Inspect nearby plants for similar symptoms and document how symptoms spread.", "Seek confirmation from a plant pathologist or local extension service before removing valuable plants or choosing a control."]
    elif any(term in lowered for term in ("mildew", "rust", "blight", "spot", "rot", "scab", "mold", "mould")):
        summary = "The image resembles a labelled leaf-disease category. Confirm the diagnosis and crop context before treatment."
        actions = [
            "Check both sides of leaves and inspect more than one plant to see whether the pattern repeats.",
            "Avoid unnecessary leaf wetness and improve airflow where suitable for the crop.",
            "Remove fallen or clearly affected plant material only when appropriate for the crop and local advice; clean tools after use.",
            "Ask a qualified local expert to confirm the disease and recommend an approved crop-specific management plan.",
        ]
    else:
        summary = "The image resembles a labelled disease category. A photo cannot establish the cause with certainty."
        actions = ["Record the crop, growth stage, recent weather and whether symptoms are spreading.", "Check irrigation, drainage and the underside of leaves; nutrient and environmental problems can resemble disease.", "Use soil or tissue test results and local expert advice before changing fertilizer or applying a treatment."]

    return {
        "title": readable_label,
        "summary": summary,
        "actions": actions,
        "safety_note": "This is educational image-classification guidance, not a confirmed diagnosis. Natural products can still harm people, plants and beneficial insects; follow local labels and expert guidance.",
    }
