var { execSync } = require('child_process');
var BotShell = require('/data/data/com.ohmnilabs.telebot_rtc/files/assets/node-files/bot_shell');
const { AutonomyController } = require('/data/data/com.ohmnilabs.telebot_rtc/files/assets/node-files/autonomy_controller');

const STACK = {
  AUTONOMY: 0,
  NORMAL: 1
};


class FollowingMePlugin {
  constructor(botnode) {
    var self = this;
    // States
    var tag = 'FolowingMePlugin';
    // Log loading msg
    console.log(tag, 'loaded!');

    AutonomyController.prototype.cmd_startFollowingMe = function (mode) {
      if (mode == 'heteronomy') {
        console.log(this.TAG, 'Start following me in HETERONOMY mode.');
        if (botnode.currentStack === STACK.AUTONOMY) botnode.switchToNormalStack();
        execSync('docker start ofm && docker exec -d ofm python3 main.py --ohmni heteronomy');
        return self.notify('start_following_me', 'success', 'heteronomy');
      }
      if (mode == 'autonomy') {
        console.log(this.TAG, 'Start following me in AUTONOMY mode.');
        if (botnode.currentStack === STACK.NORMAL) botnode.switchAutonomyStack();
        execSync('docker start ofm && docker exec -d ofm python3 main.py --ohmni autonomy');
        return self.notify('start_following_me', 'success', 'autonomy');
      }
    }
    AutonomyController.prototype.cmd_stopFollowingMe = function () {
      console.log(this.TAG, 'Stop following me.');
      execSync('docker stop ofm');
      return self.notify('stop_following_me', 'success');
    }

    // Auto open camera before start following me
    BotShell.prototype.cmd_start_following_me = function (params) {
      if (params.length != 1)
        return this.log(tag, 'start_following_me <following me mode>');
      this.cmd_camera_start([]);
      botnode.autonomyController.cmd_startFollowingMe(params[0]);
    }
    // Assume that camera is opened before we start following me
    BotShell.prototype.cmd_start_following_me_ll = function (params) {
      if (params.length != 1)
        return this.log(tag, 'start_following_me_ll <following me mode>');
      botnode.autonomyController.cmd_startFollowingMe(params[0]);
    }
    // Stop
    BotShell.prototype.cmd_stop_following_me = function (params) {
      botnode.autonomyController.cmd_stopFollowingMe();
    }

  }

  notify(botnode, funcName, status, mode = '') {
    return botnode._api.sendJson({
      type: 'autonomy_bot_response',
      msg: {
        type: funcName,
        msg: {
          status: status,
          message: mode,
        }
      }
    });
  }
}

module.exports = FollowingMePlugin;