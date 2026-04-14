const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function createMission(prompt: string): Promise<{ mission_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/api/missions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  })
  if (!res.ok) throw new Error('Failed to create mission')
  return res.json()
}

export async function getMission(missionId: string) {
  const res = await fetch(`${API_BASE}/api/missions/${missionId}`)
  if (!res.ok) throw new Error('Mission not found')
  return res.json()
}

export async function getMissionFiles(missionId: string): Promise<{ files: Record<string, string> }> {
  const res = await fetch(`${API_BASE}/api/missions/${missionId}/files`)
  if (!res.ok) throw new Error('Failed to fetch files')
  return res.json()
}
