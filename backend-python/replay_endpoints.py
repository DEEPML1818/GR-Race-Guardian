# Race Replay Builder Endpoints
# Add these to app.py before the if __name__ == '__main__' block

from grracing.race_replay_builder import RaceReplayBuilder

class ReplayBuildRequest(BaseModel):
    track_id: str
    race_id: str


@app.post('/replay/build')
async def build_race_replay(req: ReplayBuildRequest):
    """
    Build race replay JSON from CSV files.
    
    Analyzes lap times and results to create complete race timeline
    with overtakes, gaps, and position changes.
    """
    try:
        builder = RaceReplayBuilder(req.track_id)
        parser = get_track_parser()
        
        # Get track directory
        track_info = parser._get_track_info(req.track_id)
        if not track_info:
            raise HTTPException(status_code=404, detail=f'Track {req.track_id} not found')
        
        track_dir = track_info['path']
        
        # Find CSV files
        results_csv = None
        lap_times_csv = None
        
        import glob
        for file in glob.glob(f"{track_dir}/*"):
            if '03_' in file and 'Results' in file and req.race_id in file:
                results_csv = file
            elif f'{req.race_id}_{req.track_id}_lap_time.csv' in file:
                lap_times_csv = file
        
        if not results_csv or not lap_times_csv:
            raise HTTPException(
                status_code=404,
                detail=f'CSV files not found for {req.track_id} {req.race_id}'
            )
        
        # Build replay
        replay_data = builder.build_replay_json(results_csv, lap_times_csv)
        
        return {
            "success": True,
            **replay_data
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f'failed to build replay: {str(e)}\n{traceback.format_exc()}'
        print(f"[API Error] {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/replay/tracks')
async def get_replay_tracks():
    """
    Get list of tracks with available replay data.
    """
    try:
        parser = get_track_parser()
        tracks = parser.get_available_tracks()
        
        return {
            "success": True,
            "tracks": tracks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
