var { spawn } = require('child_process');
var LogCatter = require('logcatter');
var Log = new LogCatter('FollowingMePlugin');

class FollowingMePlugin {

  constructor(botnode) {
    // States
    var python3 = null;
    // Log loading msg
    Log.i("  -> FollowingMePlugin loaded!");
    // Bind some extra bot shell commands
    botnode._botshell.cmd_start_following_me = function (params, rl) {
      this.log(rl, 'Start following me.');
      python3 = spawn('python3', ['/home/ohmnidev/ohmni-follows-me/main.py', '--ohmni', 'start']);
    }
    botnode._botshell.cmd_stop_following_me = function (params, rl) {
      if (!python3) return this.log(rl, 'Following me process have not started yet.');
      this.log(rl, 'Stop following me.');
      python3.kill();
    }
  }

}

module.exports = FollowingMePlugin;