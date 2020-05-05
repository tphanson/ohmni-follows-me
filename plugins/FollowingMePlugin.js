var { spawn } = require('child_process');
var LogCatter = require('logcatter');
var Log = new LogCatter('FollowingMePlugin');

class FollowingMePlugin {

  constructor(botnode) {
    // States
    this.botnode = botnode;
    this.python3 = null;
    // Log loading msg
    Log.i("  -> FollowingMePlugin loaded!");
    // Bind some extra bot shell commands
    this.start_cmd();
    this.stop_cmd();
  }

  start_cmd = () => {
    this.botnode._botshell.cmd_start_following_me = (params, rl) => {
      this.log(rl, 'Start following me.');
      this.python3 = spawn('python3', ['/home/ohmnidev/ohmni-follows-me/main.py', '--ohmni', 'start']);
    }
  }

  stop_cmd = () => {
    this.botnode._botshell.cmd_stop_following_me = (params, rl) => {
      if (!this.python3) return this.log(rl, 'Following me process have not started yet.');
      this.log(rl, 'Stop following me.');
      this.python3.kill();
    }
  }

}

module.exports = FollowingMePlugin;