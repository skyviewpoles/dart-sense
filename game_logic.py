import json
import os

class GameLogic:
    def __init__(self, player_names, num_players=2):
        self.player_names = player_names[:num_players] # list of names/initials, up to 6
        self.num_players = len(self.player_names)
        self.current_player_idx = 0
        self.darts_thrown_this_turn = 0
        self.max_darts_per_turn = 5

        # Golf Cricket setup: sectors/holes, marks needed (3 per hole), par-5 style
        self.holes = [20, 19, 18, 17, 16, 15, 'bull'] # bull = 25/50
        self.marks_needed = {h: 3 for h in self.holes}
        self.marks = {name: {h: 0 for h in self.holes} for name in self.player_names}
        self.scores = {name: 0 for name in self.player_names} # total "strokes"/penalty points; lower better
        self.bust_limits = {h: 10 for h in self.holes if h != 'bull'}
        self.bust_limits['bull'] = 20

        # Game state
        self.game_over = False
        self.winner = None

        # All-time lowest scores (personal bests - lower is better)
        self.all_time_file = "grice_games_all_time.json"
        self.all_time_lows = self._load_all_time_lows()
        self.personal_bests = {name: self.all_time_lows.get(name, float('inf')) for name in self.player_names}

    def _load_all_time_lows(self):
        if os.path.exists(self.all_time_file):
            try:
                with open(self.all_time_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_all_time_lows(self):
        with open(self.all_time_file, 'w') as f:
            json.dump(self.all_time_lows, f, indent=4)

    def register_dart(self, score):
        """Called by video_processing when a dart hit is confirmed. score = int (e.g. 60 for T20, 50 for bull, etc.)"""
        if self.game_over:
            return

        player = self.player_names[self.current_player_idx]

        # Determine which hole/sector this dart counts for (simplified - expand for exact Cricket logic)
        # For example: if score in [20,40,60] -> hole=20, marks=1/2/3
        hole = None
        marks_this_dart = 1
        if score == 50:
            hole = 'bull'
            marks_this_dart = 2 # bullseye = double bull? Adjust as needed
        elif score % 20 == 0 and score // 20 in range(1, 4): # e.g. 20,40,60
            hole = score // (marks_this_dart if marks_this_dart > 1 else 1)
        # ... add more precise logic here for doubles/triples/outer bull

        if hole and hole in self.holes:
            current_marks = self.marks[player][hole]
            new_marks = min(current_marks + marks_this_dart, 3) # cap at 3
            added_marks = new_marks - current_marks

            if added_marks > 0:
                # Award "strokes" only on excess marks (golf penalty style)
                excess = max(0, (current_marks + marks_this_dart) - 3)
                penalty = excess * (self.bust_limits.get(hole, 10) if excess > 0 else 0)
                self.scores[player] += penalty

                self.marks[player][hole] = new_marks

        self.darts_thrown_this_turn += 1

        # Check if turn ends: 5 darts thrown OR 3 marks on current target(s) OR bust
        # (your rule: keep throwing until 3 marks or bust, but max 5)
        if self.darts_thrown_this_turn >= self.max_darts_per_turn or self._check_bust_or_complete():
            self.end_turn()

    def _check_bust_or_complete(self):
        # Placeholder: return True if bust occurred this turn or all needed marks hit
        # Customize: e.g. if any hole exceeded bust limit this turn
        return False # expand with your bust logic

    def end_turn(self):
        self.darts_thrown_this_turn = 0
        self.current_player_idx = (self.current_player_idx + 1) % self.num_players

        # Check if game is over (all holes have 3 marks for someone? or manual end)
        if self._is_game_over():
            self.game_over = True
            self.end_game()

    def _is_game_over(self):
        # Example condition: all holes closed (3 marks) by at least one player, then lowest score wins
        # Customize to your exact win condition
        return all(all(m >= 3 for m in player_marks.values()) for player_marks in self.marks.values())

    def end_game(self):
        # Update all-time lows for every player (lowest = best)
        for name in self.player_names:
            final = self.scores[name]
            if final < self.personal_bests.get(name, float('inf')):
                self.personal_bests[name] = final
                self.all_time_lows[name] = final
                print(f"New Grice Games record for {name}: {final}!") # can add TTS

        self._save_all_time_lows()

    def get_all_time_summary(self):
        if not self.all_time_lows:
            return "No Grice Games records yet."
        lines = ["Grice Games All-Time Lowest Scores (Best):"]
        sorted_records = sorted(self.all_time_lows.items(), key=lambda x: x[1])
        for name, score in sorted_records:
            lines.append(f"{name}: {score}")
        return "\n".join(lines)

    # Add other methods as needed (get_current_player, get_scores_str, etc.)

    def play(self):
        
        while True:
            darts = input(f"{self.player_names[self.current_player]}, enter your darts: ")
            self.commit_score(darts)

if __name__ == "__main__":
    game = GameLogic('x01', ['Ben', 'Will'], 301, 2)
    game.play()
