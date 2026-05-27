import logging
from datetime import datetime, timezone, timedelta

import requests

from plugins.base_plugin.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class Spoolman(BasePlugin):
    def generate_settings_template(self):
        template_params = super().generate_settings_template()
        return template_params

    def _pick(self, obj, path, default=None):
        cur = obj
        for part in path.split("."):
            if not isinstance(cur, dict):
                return default
            cur = cur.get(part)
            if cur is None:
                return default
        return cur

    def _norm(self, value):
        return " ".join(str(value or "").strip().split())

    def _read_display_mode(self, settings, key, default_value="show"):
        raw = settings.get(key, default_value)

        if isinstance(raw, list):
            raw = raw[-1] if raw else default_value

        value = str(raw or default_value).strip().lower()
        return "hide" if value == "hide" else "show"

    def _parse_iso(self, value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            return None

    def _format_age(self, last_used_dt):
        if not last_used_dt:
            return "No recent use"

        now = datetime.now(timezone.utc)
        delta = now - last_used_dt
        minutes = int(delta.total_seconds() // 60)

        if minutes < 1:
            return "Used just now"
        if minutes < 60:
            return f"Used {minutes}m ago"

        hours = minutes // 60
        mins = minutes % 60
        if hours < 24:
            if mins == 0:
                return f"Used {hours}h ago"
            return f"Used {hours}h {mins}m ago"

        days = hours // 24
        return f"Used {days}d ago"

    def _format_active_window_label(self, minutes):
        minutes = int(minutes)

        if minutes < 60:
            unit = "minute" if minutes == 1 else "minutes"
            return f"Last {minutes} {unit}"

        if minutes % 1440 == 0:
            days = minutes // 1440
            unit = "day" if days == 1 else "days"
            return f"Last {days} {unit}"

        if minutes % 60 == 0:
            hours = minutes // 60
            unit = "hour" if hours == 1 else "hours"
            return f"Last {hours} {unit}"

        return f"Last {minutes} minutes"

    def _color_hex(self, spool):
        filament = spool.get("filament") or {}
        hex_color = (
            filament.get("color_hex")
            or spool.get("color_hex")
            or filament.get("color")
            or spool.get("color")
            or "#cccccc"
        )
        hex_color = str(hex_color).strip()

        if not hex_color:
            return "#cccccc"
        if not hex_color.startswith("#"):
            hex_color = "#" + hex_color
        if len(hex_color) not in (4, 7):
            return "#cccccc"

        return hex_color

    def _color_name(self, spool):
        filament = spool.get("filament") or {}
        return self._norm(
            filament.get("color_name")
            or spool.get("color_name")
            or filament.get("color")
            or spool.get("color")
            or filament.get("name")
            or ""
        )

    def _brand_name(self, spool):
        filament = spool.get("filament") or {}
        vendor = filament.get("vendor")

        if isinstance(vendor, dict):
            vendor_name = vendor.get("name")
        else:
            vendor_name = vendor

        return self._norm(
            vendor_name
            or self._pick(spool, "vendor.name")
            or spool.get("vendor_name")
            or spool.get("brand")
            or ""
        )

    def _material_name(self, spool):
        return self._norm(
            self._pick(spool, "filament.material")
            or spool.get("material")
            or ""
        ).upper()

    def _spool_active(self, spool, active_minutes):
        archived = bool(spool.get("archived"))
        last_used_dt = self._parse_iso(spool.get("last_used"))
        if archived or not last_used_dt:
            return False

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=float(active_minutes))
        return last_used_dt >= cutoff

    def _record_for(self, spool, render_controls):
        material = self._material_name(spool)
        brand = self._brand_name(spool)
        color_name = self._color_name(spool)
        hex_color = self._color_hex(spool)

        grams = float(spool.get("remaining_weight") or spool.get("remainingWeight") or 0) or 0
        location = self._norm(spool.get("location") or "")
        last_used_raw = spool.get("last_used")
        last_used_dt = self._parse_iso(last_used_raw)
        spool_id = spool.get("id")

        show_material = render_controls.get("material") == "show"
        show_brand = render_controls.get("brand") == "show"
        show_color = render_controls.get("color") == "show"
        show_spool_id = render_controls.get("spool_id") == "show"
        show_grams = render_controls.get("grams") == "show"
        show_last_used = render_controls.get("last_used") == "show"
        show_location = render_controls.get("location") == "show"

        display_title = color_name if (show_color and color_name) else ""
        display_material = material if show_material else ""
        display_brand = brand if show_brand else ""
        display_spool_id = str(spool_id) if show_spool_id and spool_id is not None else ""
        display_grams = f"{round(grams):.0f}g" if show_grams else ""
        display_last_used = self._format_age(last_used_dt) if show_last_used else ""
        display_location = location if show_location else ""

        has_any_text = any([
            display_title,
            display_material,
            display_brand,
            display_spool_id,
            display_grams,
            display_last_used,
            display_location,
        ])

        return {
            "id": spool_id,
            "hex": hex_color,
            "displayTitle": display_title,
            "displayMaterial": display_material,
            "displayBrand": display_brand,
            "displaySpoolId": display_spool_id,
            "displayGrams": display_grams,
            "displayLastUsed": display_last_used,
            "displayLocation": display_location,
            "hasAnyText": has_any_text,
            "lastUsedDt": last_used_dt,
        }

    def _process_spools(self, spools, render_controls, active_minutes):
        items = [
            self._record_for(spool, render_controls)
            for spool in (spools or [])
            if self._spool_active(spool, active_minutes)
        ]

        items.sort(
            key=lambda a: (
                a["lastUsedDt"] is None,
                -(a["lastUsedDt"].timestamp() if a["lastUsedDt"] else 0),
                a["id"] if a["id"] is not None else 0,
            )
        )
        return items

    def _layout_mode(self, item_count):
        if item_count <= 1:
            return "hero"
        if item_count == 2:
            return "duo"
        if item_count <= 4:
            return "quad"
        if item_count <= 6:
            return "grid"
        return "dense"

    def _get_spools(self, base_url):
        api_base = base_url.rstrip("/") + "/api/v1"
        url = api_base + "/spool"

        try:
            response = requests.get(
                url,
                params={"allow_archived": "false"},
                headers={"Accept": "application/json"},
                timeout=10,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout as exc:
            logger.exception("Spoolman request timed out")
            raise RuntimeError("Spoolman did not respond in time. Check the URL and that the server is online.") from exc
        except requests.exceptions.ConnectionError as exc:
            logger.exception("Spoolman connection failed")
            raise RuntimeError("Could not connect to Spoolman. Check the URL/hostname and make sure the server is reachable.") from exc
        except requests.exceptions.HTTPError as exc:
            logger.exception("Spoolman returned HTTP error")
            status = exc.response.status_code if exc.response is not None else "unknown"
            raise RuntimeError(f"Spoolman returned an HTTP {status} error.") from exc
        except requests.exceptions.RequestException as exc:
            logger.exception("Spoolman request failed")
            raise RuntimeError("Failed to contact Spoolman. Check the URL and server status.") from exc

        try:
            data = response.json()
        except ValueError as exc:
            logger.exception("Spoolman returned invalid JSON")
            raise RuntimeError("Spoolman returned invalid data.") from exc

        if isinstance(data, dict) and "items" in data:
            return data["items"]
        if isinstance(data, list):
            return data

        raise RuntimeError("Spoolman returned data in an unexpected format.")

    def generate_image(self, settings, device_config):
        spoolman_url = str(settings.get("spoolman_url", "") or "").strip()
        if not spoolman_url:
            raise RuntimeError("Spoolman URL is required")

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        title_text = str(settings.get("title_text", "RECENT ACTIVE FILAMENTS") or "RECENT ACTIVE FILAMENTS")

        try:
            active_minutes = int(settings.get("active_minutes") or 60)
        except (TypeError, ValueError):
            active_minutes = 60

        if active_minutes < 1:
            active_minutes = 60

        render_controls = {
            "material": self._read_display_mode(settings, "display_material", "show"),
            "brand": self._read_display_mode(settings, "display_brand", "show"),
            "color": self._read_display_mode(settings, "display_color", "show"),
            "spool_id": self._read_display_mode(settings, "display_spool_id", "show"),
            "grams": self._read_display_mode(settings, "display_grams", "show"),
            "last_used": self._read_display_mode(settings, "display_last_used", "show"),
            "location": self._read_display_mode(settings, "display_location", "show"),
        }

        logger.warning("SPOOLMAN SETTINGS: %r", settings)
        logger.warning("SPOOLMAN RENDER CONTROLS: %r", render_controls)

        try:
            spools = self._get_spools(spoolman_url)
            items = self._process_spools(spools, render_controls, active_minutes)
            logger.warning("SPOOLMAN FIRST ITEM: %r", items[0] if items else None)
        except RuntimeError:
            raise
        except Exception as exc:
            logger.exception("Failed to load Spoolman spools")
            raise RuntimeError("Unable to load Spoolman data.") from exc

        template_params = {
            "title": title_text,
            "items": items,
            "item_count": len(items),
            "active_minutes": active_minutes,
            "active_window_label": self._format_active_window_label(active_minutes),
            "layout_mode": self._layout_mode(len(items)),
            "plugin_settings": settings,
        }

        image = self.render_image(
            dimensions,
            "spoolman_active_spools.html",
            "spoolman_active_spools.css",
            template_params,
        )

        if not image:
            raise RuntimeError("Failed to take screenshot, please check logs.")
        return image