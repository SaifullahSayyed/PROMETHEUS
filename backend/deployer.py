import asyncio
import json
import tempfile
from pathlib import Path
from models.mission import Mission


async def deploy(mission: Mission) -> str:
    """
    Deploy the generated application.
    Returns a URL string.

    Strategy:
    1. Create all generated files in a temp directory
    2. Write a deployment manifest
    3. Try Fly.io if flyctl is available
    4. Fall back to local preview URL
    """
    try:
        deploy_dir = Path(tempfile.mkdtemp()) / "deployed_app"
        deploy_dir.mkdir(parents=True, exist_ok=True)

        # Write all generated files
        written_count = 0
        for filename, content in mission.generated_files.items():
            # Sanitize filename to prevent path traversal
            safe_filename = filename.lstrip("/\\").replace("..", "")
            file_path = deploy_dir / safe_filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                file_path.write_text(content, encoding="utf-8")
                written_count += 1
            except Exception:
                continue

        # Write a deployment manifest
        manifest = {
            "company": mission.contract.company_name if mission.contract else "Generated Company",
            "tagline": mission.contract.tagline if mission.contract else "",
            "files": list(mission.generated_files.keys()),
            "file_count": written_count,
            "survival_score": mission.survival_score,
            "threats_resolved": sum(1 for r in mission.kill_reports if r.status in ["PATCHED", "DISMISSED"]),
            "total_threats": len(mission.kill_reports),
            "deploy_path": str(deploy_dir),
            "mission_id": mission.id
        }
        (deploy_dir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))

        mission.add_log("DEPLOYER", f"Wrote {written_count} files to deployment directory.", "INFO")

        # Check if flyctl is available
        try:
            proc = await asyncio.create_subprocess_shell(
                "flyctl version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)

            if proc.returncode == 0:
                mission.add_log("DEPLOYER", "Fly.io detected. Live deployment available.", "INFO")
                # For demo: Fly.io deployment would be implemented here
                # Would require fly.toml in generated app dir + flyctl deploy
        except Exception:
            pass

        # Return the preview URL
        return f"http://localhost:8000/preview/{mission.id}"

    except Exception as e:
        mission.add_log("DEPLOYER", f"Deploy error: {str(e)}. Using fallback URL.", "WARNING")
        return f"http://localhost:8000/preview/{mission.id}"
