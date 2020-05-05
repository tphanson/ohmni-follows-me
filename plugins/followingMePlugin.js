var { exec } = require('child_process');
var BotShell = require('/data/data/com.ohmnilabs.telebot_rtc/files/assets/node-files/bot_shell');

class FollowingMePlugin {

  constructor(botnode) {
    // States
    var tag = 'FolowingMePlugin';
    // Log loading msg
    console.log(tag, 'loaded!');
    // Bind some extra bot shell commands
    BotShell.prototype.cmd_start_following_me = function (params) {
      console.log(tag, 'Start following me.');
      exec('docker start dev');
    }
    BotShell.prototype.cmd_stop_following_me = function (params) {
      console.log(tag, 'Stop following me.');
      exec('docker stop dev');
    }
  }

}

module.exports = FollowingMePlugin;