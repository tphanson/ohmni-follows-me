var { spawn } = require('child_process');
var BotShell = require('/data/data/com.ohmnilabs.telebot_rtc/files/assets/node-files/bot_shell');

class FollowingMePlugin {

  constructor(botnode) {
    // States
    var tag = 'FolowingMePlugin';
    var python3 = null;
    // Log loading msg
    Log.i("  -> FollowingMePlugin loaded!");
    // Bind some extra bot shell commands
    BotShell.prototype._botshell.cmd_start_following_me = function (params) {
      console.log(tag, 'Start following me.');
      python3 = spawn('python3', ['/home/ohmnidev/ohmni-follows-me/main.py', '--ohmni', 'start']);
    }
    BotShell.prototype._botshell.cmd_stop_following_me = function (params) {
      if (!python3) return console.log(tag, 'Following me process have not started yet.');
      console.log(tag, 'Stop following me.');
      python3.kill();
      python3 = null;
    }
  }

}

module.exports = FollowingMePlugin;