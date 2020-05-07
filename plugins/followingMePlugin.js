var { exec } = require('child_process');
var BotShell = require('/data/data/com.ohmnilabs.telebot_rtc/files/assets/node-files/bot_shell');

class FollowingMePlugin {
  constructor() {
    // States
    var tag = 'FolowingMePlugin';
    // Log loading msg
    console.log(tag, 'loaded!');
    // Bind some extra bot shell commands
    BotShell.prototype.cmd_start_following_me = function (params) {
      if (params[0] == 'heteronomy') {
        console.log(tag, 'Start following me in HETERONOMY mode.');
        exec('docker start ofm && docker exec -dt ofm python3 main.py --ohmni heteronomy');
      }
      if (params[0] == 'autonomy') {
        console.log(tag, 'Start following me in AUTONOMY mode.');
        exec('docker start ofm && docker exec -dt ofm python3 main.py --ohmni autonomy');
      }
    }
    BotShell.prototype.cmd_stop_following_me = function (params) {
      console.log(tag, 'Stop following me.');
      exec('docker stop ofm');
    }
  }

}

module.exports = FollowingMePlugin;