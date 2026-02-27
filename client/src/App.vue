<template>
  <!-- Confirm dialogs (global, rendered outside layout) -->
  <ConfirmPopup></ConfirmPopup>

  <!-- Generic Confirm Modal -->
  <teleport to="body">
    <div v-if="confirm.show" class="modal-backdrop" @click.self="confirmReject">
      <div class="modal">
        <div class="modal-header">
          <span>{{ confirm.header }}</span>
        </div>
        <div class="modal-body">
          <div class="confirm-box">
            <div class="confirm-icon" :class="confirm.danger ? '' : 'warn'">
              <i class="pi pi-exclamation-circle"></i>
            </div>
            <div class="confirm-title">{{ confirm.header }}</div>
            <div class="confirm-msg">{{ confirm.message }}</div>
          </div>
        </div>
        <div class="modal-footer">
          <button
            v-if="confirm.acceptLabel !== null"
            class="btn btn-danger"
            @click="confirmAccept"
          >
            {{ confirm.acceptLabel || "Confirm" }}
          </button>
          <button class="btn btn-ghost" @click="confirmReject">
            {{ confirm.rejectLabel || "Cancel" }}
          </button>
        </div>
      </div>
    </div>

    <!-- Settings Modal -->
    <div
      v-if="modal_settings"
      class="modal-backdrop"
      @click.self="modal_settings = false"
    >
      <div class="modal">
        <div class="modal-header">
          <span>System Settings</span>
          <button
            class="btn btn-ghost btn-sm btn-icon"
            @click="modal_settings = false"
          >
            <i class="pi pi-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="field-row">
            <label class="field-label">Listen IP:Port</label>
            <div class="field-value">
              <input
                class="ctrl"
                v-model="config_manager.listen"
                placeholder="0.0.0.0:1234"
              />
              <div class="mt-2 text-muted" style="font-size: 11px">
                Use 0.0.0.0 for network access
              </div>
            </div>
          </div>
          <div class="field-row">
            <label class="field-label">Poll Time</label>
            <div class="field-value">
              <input
                class="ctrl ctrl-num"
                type="number"
                v-model.number="config_manager.poll"
                min="0"
              />
              ms
            </div>
          </div>
          <div class="field-row">
            <label class="field-label">Screen Refresh</label>
            <div class="field-value">
              <input
                class="ctrl ctrl-num"
                type="number"
                v-model.number="config_manager.refresh"
                min="0"
              />
              ms
            </div>
          </div>
          <div class="field-row">
            <label class="field-label">Heartbeat</label>
            <div class="field-value">
              <input
                class="ctrl ctrl-num"
                type="number"
                v-model.number="config_manager.heartbeat"
                min="0"
              />
              ms
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button
            class="btn btn-primary"
            :disabled="config_manager.saving"
            @click="onSaveConfig"
          >
            <i class="pi pi-save"></i> Save
          </button>
          <button class="btn btn-ghost" @click="modal_settings = false">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Sensor Manage Modal -->
    <div
      v-if="sensor_manage.show"
      class="modal-backdrop"
      @click.self="sensor_manage.show = false"
    >
      <div class="modal modal-lg">
        <div class="modal-header">
          <span>Sensor Instances</span>
          <div class="flex gap-2">
            <button class="btn btn-success btn-sm" @click="onOpenAddSensor">
              <i class="pi pi-plus"></i> Add
            </button>
            <button
              class="btn btn-ghost btn-sm btn-icon"
              @click="sensor_manage.show = false"
            >
              <i class="pi pi-times"></i>
            </button>
          </div>
        </div>
        <div class="modal-body" style="padding: 0">
          <table class="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Description</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in sensor_manage.list" :key="row.name">
                <td class="mono" style="color: var(--accent)">
                  {{ row.name }}
                </td>
                <td>
                  <span class="flex gap-2" style="align-items: center">
                    <i
                      v-if="row.info.icon"
                      :class="'pi ' + row.info.icon"
                      style="color: var(--text-muted)"
                    ></i>
                    {{ row.info.name }}
                  </span>
                </td>
                <td style="color: var(--text-secondary)">
                  {{ row.info.description }}
                </td>
                <td>
                  <div class="flex gap-2">
                    <button
                      v-if="row.info.fields && row.info.fields.length"
                      class="btn btn-ghost btn-sm"
                      @click="onSensorEdit(row)"
                    >
                      <i class="pi pi-pencil"></i>
                    </button>
                    <button
                      v-if="row.info.multiple"
                      class="btn btn-danger btn-sm"
                      @click="onSensorRemove(row)"
                    >
                      <i class="pi pi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Add Sensor Modal -->
    <div
      v-if="sensor_manage.show_add"
      class="modal-backdrop"
      @click.self="sensor_manage.show_add = false"
    >
      <div class="modal">
        <div class="modal-header">
          <span>Add Sensor Instance</span>
          <button
            class="btn btn-ghost btn-sm btn-icon"
            @click="sensor_manage.show_add = false"
          >
            <i class="pi pi-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="mb-3">
            <label class="field-label mb-2" style="display: block"
              >Sensor Type</label
            >
            <select
              class="ctrl"
              v-model="sensor_manage.picked"
              @change="onSensorAddChange"
            >
              <option value="" disabled>Pick a sensor…</option>
              <option
                v-for="s in sensor_manage.sensors"
                :key="s.id"
                :value="s.id"
              >
                {{ s.name }}
              </option>
            </select>
          </div>
          <template v-if="sensor_manage.picked && sensor_manage.config_data">
            <div
              v-for="(item, i) in sensor_manage.config_data.fields"
              :key="i"
              class="field-row"
            >
              <label class="field-label">{{ item.name }}</label>
              <div class="field-value">
                <input
                  v-if="item.type === 'string'"
                  class="ctrl"
                  type="text"
                  v-model="item.value"
                />
                <input
                  v-else-if="item.type === 'number'"
                  class="ctrl ctrl-num"
                  type="number"
                  v-model.number="item.value"
                />
                <select
                  v-else-if="item.type === 'list'"
                  class="ctrl"
                  v-model="item.value"
                >
                  <option v-for="opt in item.list" :key="opt" :value="opt">
                    {{ opt }}
                  </option>
                </select>
                <label v-else-if="item.type === 'boolean'" class="toggle">
                  <input type="checkbox" v-model="item.value" />
                  <span class="toggle-slider"></span>
                </label>
                <span v-else class="mono text-muted">{{ item.value }}</span>
              </div>
            </div>
          </template>
        </div>
        <div class="modal-footer">
          <button
            class="btn btn-primary"
            :disabled="!sensor_manage.picked"
            @click="onAddSensor"
          >
            <i class="pi pi-check"></i> Add
          </button>
          <button class="btn btn-ghost" @click="sensor_manage.show_add = false">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Edit Sensor Modal -->
    <div
      v-if="sensor_manage.show_edit && sensor_manage.edit"
      class="modal-backdrop"
      @click.self="sensor_manage.show_edit = false"
    >
      <div class="modal">
        <div class="modal-header">
          <span
            >Edit Sensor —
            <span class="text-accent mono">{{
              sensor_manage.edit.name
            }}</span></span
          >
          <button
            class="btn btn-ghost btn-sm btn-icon"
            @click="sensor_manage.show_edit = false"
          >
            <i class="pi pi-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div
            v-for="(item, i) in sensor_manage.edit.info.fields"
            :key="i"
            class="field-row"
          >
            <label class="field-label">{{ item.name }}</label>
            <div class="field-value">
              <input
                v-if="item.type === 'string'"
                class="ctrl"
                type="text"
                v-model="item.value"
              />
              <input
                v-else-if="item.type === 'number'"
                class="ctrl ctrl-num"
                type="number"
                v-model.number="item.value"
              />
              <select
                v-else-if="item.type === 'list'"
                class="ctrl"
                v-model="item.value"
              >
                <option v-for="opt in item.list" :key="opt" :value="opt">
                  {{ opt }}
                </option>
              </select>
              <label v-else-if="item.type === 'boolean'" class="toggle">
                <input type="checkbox" v-model="item.value" />
                <span class="toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary" @click="onSensorSave">
            <i class="pi pi-save"></i> Save
          </button>
          <button
            class="btn btn-ghost"
            @click="sensor_manage.show_edit = false"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Add Widget Modal -->
    <div
      v-if="widget_manage.show"
      class="modal-backdrop"
      @click.self="widget_manage.show = false"
    >
      <div class="modal">
        <div class="modal-header">
          <span>Add Widget</span>
          <button
            class="btn btn-ghost btn-sm btn-icon"
            @click="widget_manage.show = false"
          >
            <i class="pi pi-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <label class="field-label mb-2" style="display: block"
            >Widget Type</label
          >
          <select class="ctrl" v-model="widget_manage.name">
            <option value="" disabled>Pick a widget…</option>
            <option v-for="w in widgets" :key="w.name" :value="w.name">
              {{ w.name }}
            </option>
          </select>
        </div>
        <div class="modal-footer">
          <button
            class="btn btn-primary"
            :disabled="!widget_manage.name"
            @click="onAddWidget"
          >
            <i class="pi pi-plus"></i> Add
          </button>
          <button class="btn btn-ghost" @click="widget_manage.show = false">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- LED Strip Modal -->
    <div
      v-if="led_manage.show"
      class="modal-backdrop"
      @click.self="led_manage.show = false"
    >
      <div class="modal">
        <div class="modal-header">
          <span>LED Strip Control</span>
          <button
            class="btn btn-ghost btn-sm btn-icon"
            @click="led_manage.show = false"
          >
            <i class="pi pi-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="section-title mb-3">Pattern</div>
          <div class="led-grid mb-3">
            <div
              v-for="opt in led_manage.list"
              :key="opt.id"
              class="led-option"
              :class="{ selected: led_manage.theme === opt.id }"
              @click="
                led_manage.theme = opt.id;
                onChangeLED();
              "
            >
              <i :class="opt.icon" class="icon"></i>
              <span>{{ opt.name }}</span>
            </div>
          </div>
          <div class="flex gap-4 mt-3" style="justify-content: center">
            <div class="knob-group">
              <SimpleKnob
                v-model="led_manage.speed"
                :min="1"
                :max="5"
                @change="onChangeLED"
              />
              <div class="knob-label">Speed</div>
            </div>
            <div class="knob-group">
              <SimpleKnob
                v-model="led_manage.intensity"
                :min="1"
                :max="5"
                @change="onChangeLED"
              />
              <div class="knob-label">Intensity</div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="led_manage.show = false">
            Close
          </button>
        </div>
      </div>
    </div>

    <!-- Manage Screens Modal -->
    <div
      v-if="screen_manage.show"
      class="modal-backdrop"
      @click.self="screen_manage.show = false"
    >
      <div class="modal">
        <div class="modal-header">
          <span>Manage Screens</span>
          <button
            class="btn btn-ghost btn-sm btn-icon"
            @click="screen_manage.show = false"
          >
            <i class="pi pi-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="flex gap-2 mb-3">
            <input
              class="ctrl"
              v-model="screen_manage.name"
              placeholder="New screen name…"
            />
            <button
              class="btn btn-success"
              :disabled="!screen_manage.name"
              @click="onAddScreen"
            >
              <i class="pi pi-plus"></i>
            </button>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in theme?.screens" :key="s.id">
                <td>{{ s.name }}</td>
                <td>
                  <span
                    v-if="screen_manage.active === s.id"
                    class="badge badge-info"
                    >Active</span
                  >
                </td>
                <td>
                  <button
                    class="btn btn-danger btn-sm"
                    :disabled="
                      screen?.id === s.id || screen_manage.active === s.id
                    "
                    @click="onDeleteScreen($event, s.id)"
                  >
                    <i class="pi pi-trash"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </teleport>

  <!-- ── App Shell ─────────────────────────────────────────── -->
  <div class="app-shell">
    <!-- ── Left Sidebar ─────────────────────────────────────── -->
    <aside class="sidebar">
      <!-- Brand Header -->
      <div class="app-header">
        <div class="app-logo">⚡</div>
        <div>
          <div class="app-title">s1<span>panel</span></div>
          <div
            style="
              font-size: 10px;
              color: var(--text-muted);
              letter-spacing: 0.06em;
            "
          >
            TFT CONTROLLER
          </div>
        </div>
        <div style="margin-left: auto">
          <span class="status-pill" :class="connected ? 'online' : 'offline'">
            <span class="status-dot"></span>
            {{ connected ? "Live" : "Off" }}
          </span>
        </div>
      </div>

      <!-- LCD Preview -->
      <div class="preview-section">
        <div class="preview-label">
          <span>LCD Preview</span>
          <span class="badge badge-info" v-if="connected">LIVE</span>
        </div>
        <div class="preview-frame">
          <canvas ref="canvas"></canvas>
          <div class="preview-overlay-live" v-if="connected">● LIVE</div>
        </div>
      </div>

      <!-- System Info -->
      <div class="info-section">
        <div class="section-title mb-2">System</div>
        <div class="info-row">
          <span class="info-key">IP</span>
          <span class="info-val truncate" style="max-width: 140px">{{
            config?.listen
          }}</span>
        </div>
        <div class="info-row">
          <span class="info-key">Theme</span>
          <span class="info-val truncate" style="max-width: 140px">{{
            shortThemeName
          }}</span>
        </div>
        <div class="info-row">
          <span class="info-key">Poll</span>
          <span class="info-val">{{ config?.poll }} ms</span>
        </div>
        <div class="info-row">
          <span class="info-key">Refresh</span>
          <span class="info-val">{{ config?.refresh }} ms</span>
        </div>
        <div class="info-row">
          <span class="info-key">LCD</span>
          <span class="info-val truncate" style="max-width: 120px">{{
            config?.device
          }}</span>
        </div>
        <div class="info-row">
          <span class="info-key">LED</span>
          <span class="info-val truncate" style="max-width: 120px">{{
            config?.led_config?.device
          }}</span>
        </div>
        <div class="info-row">
          <span class="info-key">Screen</span>
          <span class="info-val">{{ screen?.name }}</span>
        </div>
        <div class="info-row">
          <span class="info-key">Orientation</span>
          <span class="info-val" style="text-transform: capitalize">{{
            theme?.orientation
          }}</span>
        </div>
      </div>

      <!-- Sidebar Actions -->
      <div class="sidebar-actions">
        <button
          class="btn btn-ghost btn-sm flex-1"
          @click="onEditConfig"
          title="System Settings"
        >
          <i class="pi pi-cog"></i> Settings
        </button>
        <button
          class="btn btn-ghost btn-sm"
          @click="onOpenSensorManage"
          title="Sensors"
        >
          <i class="pi pi-bolt" style="color: var(--accent)"></i>
        </button>
        <button
          class="btn btn-ghost btn-sm"
          @click="onOpenLED"
          title="LED Strip"
        >
          <i class="pi pi-sun" style="color: #facc15"></i>
        </button>
      </div>
    </aside>

    <!-- ── Main Panel ────────────────────────────────────────── -->
    <main class="main-panel">
      <!-- Tab Navigation -->
      <nav class="tab-nav">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'config' }"
          @click="activeTab = 'config'"
        >
          <i class="pi pi-sliders-h mr-1"></i> Configuration
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'screens' }"
          @click="activeTab = 'screens'"
        >
          <i class="pi pi-desktop mr-1"></i> Screens
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'widgets' }"
          @click="activeTab = 'widgets'"
        >
          <i class="pi pi-th-large mr-1"></i> Widgets
          <span
            v-if="screen?.widgets?.length"
            class="badge badge-info ml-2"
            style="padding: 1px 6px; font-size: 10px"
            >{{ screen.widgets.length }}</span
          >
        </button>
      </nav>

      <!-- ── CONFIG TAB ──────────────────────────────────────── -->
      <div v-if="activeTab === 'config'" class="tab-content">
        <!-- Unsaved banner -->
        <div v-if="unsaved_changes" class="unsaved-banner mb-3">
          <div class="flex gap-2" style="align-items: center">
            <i
              class="pi pi-exclamation-triangle"
              style="color: var(--warning)"
            ></i>
            <span
              style="color: var(--warning); font-weight: 600; font-size: 13px"
              >Unsaved changes</span
            >
          </div>
          <div class="flex gap-2">
            <button class="btn btn-success btn-sm" @click="onSaveTheme">
              <i class="pi pi-save"></i> Save
            </button>
            <button class="btn btn-ghost btn-sm" @click="onRevertTheme">
              <i class="pi pi-undo"></i> Revert
            </button>
          </div>
        </div>

        <div class="card">
          <div class="card-header">Theme & Display</div>
          <div class="card-body">
            <div class="field-row">
              <label class="field-label">Theme</label>
              <div class="field-value">
                <select
                  class="ctrl"
                  v-model="edit_theme"
                  @change="onThemeChange"
                >
                  <option
                    v-for="t in config?.theme_list"
                    :key="t.config"
                    :value="t.config"
                  >
                    {{ t.name }}
                  </option>
                </select>
              </div>
            </div>
            <div class="field-row">
              <label class="field-label">Orientation</label>
              <div class="field-value">
                <select
                  class="ctrl"
                  v-model="edit_orientation"
                  @change="onOrientationChange"
                >
                  <option value="landscape">Landscape</option>
                  <option value="portrait">Portrait</option>
                </select>
              </div>
            </div>
            <div class="field-row">
              <label class="field-label">Refresh Method</label>
              <div class="field-value">
                <select
                  class="ctrl"
                  v-model="edit_refresh"
                  @change="onRefreshChange"
                >
                  <option value="redraw">Redraw (full)</option>
                  <option value="update">Update (partial)</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">Available Sensors</div>
          <div class="card-body" style="padding: 0">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Sensor Name</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in sensors" :key="s.name">
                  <td
                    class="mono"
                    style="color: var(--accent); font-size: 12px"
                  >
                    {{ s.name }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ── SCREENS TAB ─────────────────────────────────────── -->
      <div v-if="activeTab === 'screens'" class="tab-content">
        <div class="section-header mb-3">
          <div class="section-title">Screens</div>
          <button class="btn btn-ghost btn-sm" @click="onOpenScreenManage">
            <i class="pi pi-cog"></i> Manage
          </button>
        </div>

        <!-- Screen Selector -->
        <div class="card mb-3">
          <div class="card-body">
            <div class="field-row">
              <label class="field-label">Active Screen</label>
              <div class="field-value">
                <select
                  class="ctrl"
                  v-model="edit_screen"
                  @change="onScreenChange"
                >
                  <option v-for="s in theme?.screens" :key="s.id" :value="s.id">
                    {{ s.name }}
                  </option>
                </select>
              </div>
            </div>
            <div class="field-row">
              <label class="field-label">Screen Name</label>
              <div class="field-value">
                <input
                  class="ctrl"
                  type="text"
                  v-model="edit_screen_name"
                  @input="onSetScreenName"
                />
              </div>
            </div>
            <div class="field-row">
              <label class="field-label">Duration</label>
              <div class="field-value flex gap-2" style="align-items: center">
                <input
                  class="ctrl ctrl-num"
                  type="number"
                  v-model.number="edit_duration"
                  min="0"
                  @input="onSetScreenDuration"
                />
                <span class="text-muted" style="font-size: 12px">ms</span>
              </div>
            </div>
            <div class="field-row">
              <label class="field-label">Background</label>
              <div class="field-value">
                <div class="color-field">
                  <input
                    type="color"
                    class="ctrl-color ctrl"
                    :value="
                      '#' + (edit_background || '000000').replace('#', '')
                    "
                    @input="
                      edit_background = $event.target.value;
                      onSetBackground();
                    "
                  />
                  <input
                    class="ctrl"
                    type="text"
                    v-model="edit_background"
                    @input="onSetBackground"
                    style="max-width: 120px"
                  />
                </div>
              </div>
            </div>
            <div class="field-row">
              <label class="field-label">Wallpaper</label>
              <div class="field-value">
                <template v-if="screen?.wallpaper">
                  <img
                    :src="'/api/wallpaper?screen=' + screen.id"
                    style="
                      height: 40px;
                      border-radius: 4px;
                      border: 1px solid var(--border);
                      margin-right: 8px;
                    "
                  />
                  <button
                    class="btn btn-danger btn-sm"
                    @click="onDeleteWallpaper($event)"
                  >
                    Remove
                  </button>
                </template>
                <template v-else>
                  <FileUpload
                    mode="basic"
                    name="uploading"
                    :url="'/api/upload_wallpaper?screen=' + screen?.id"
                    accept="image/png"
                    :maxFileSize="1000000"
                    @upload="onUploadWallpaper"
                    :auto="true"
                    chooseLabel="Upload PNG"
                  />
                </template>
              </div>
            </div>
            <div class="field-row">
              <label class="field-label">LED Strip</label>
              <div class="field-value">
                <button class="btn btn-ghost btn-sm" @click="onOpenLED">
                  <i class="pi pi-sun" style="color: #facc15"></i> Configure LED
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ── WIDGETS TAB ─────────────────────────────────────── -->
      <div v-if="activeTab === 'widgets'" class="tab-content">
        <div class="section-header mb-3">
          <div class="section-title">
            Widgets —
            <span class="text-accent" style="font-weight: 700">{{
              screen?.name
            }}</span>
          </div>
          <button class="btn btn-success btn-sm" @click="onShowAddWidget">
            <i class="pi pi-plus"></i> Add Widget
          </button>
        </div>

        <!-- Widget list (accordion) -->
        <div v-if="!screen?.widgets?.length" class="card">
          <div
            class="card-body"
            style="text-align: center; color: var(--text-muted); padding: 32px"
          >
            <i
              class="pi pi-inbox"
              style="font-size: 32px; margin-bottom: 10px; display: block"
            ></i>
            No widgets on this screen yet.
          </div>
        </div>

        <div
          v-for="(widget, index) in screen?.widgets"
          :key="widget.id"
          class="widget-accordion"
        >
          <div
            class="widget-header"
            :class="{ open: openWidgets.includes(widget.id) }"
            @click="toggleWidget(widget.id)"
          >
            <span
              class="widget-chevron"
              :class="{ open: openWidgets.includes(widget.id) }"
            >
              <i class="pi pi-chevron-right" style="font-size: 11px"></i>
            </span>
            <span class="widget-name">{{ widget.name }}</span>
            <span class="widget-sub">{{ widget.value || "—" }}</span>
            <div class="flex gap-1 ml-2" @click.stop>
              <button
                class="btn btn-ghost btn-sm btn-icon"
                title="Move Top"
                :disabled="isFirst(widget.id)"
                @click="onSwapTop(widget.id, 1 + index)"
              >
                <i class="pi pi-angle-double-up" style="font-size: 10px"></i>
              </button>
              <button
                class="btn btn-ghost btn-sm btn-icon"
                title="Move Up"
                :disabled="isFirst(widget.id)"
                @click="onSwapUp(widget.id, 1 + index)"
              >
                <i class="pi pi-angle-up" style="font-size: 10px"></i>
              </button>
              <button
                class="btn btn-ghost btn-sm btn-icon"
                title="Move Down"
                :disabled="isLast(widget.id)"
                @click="onSwapDown(widget.id, 1 + index)"
              >
                <i class="pi pi-angle-down" style="font-size: 10px"></i>
              </button>
              <button
                class="btn btn-ghost btn-sm btn-icon"
                title="Move Bottom"
                :disabled="isLast(widget.id)"
                @click="onSwapBottom(widget.id, 1 + index)"
              >
                <i class="pi pi-angle-double-down" style="font-size: 10px"></i>
              </button>
              <button
                class="btn btn-danger btn-sm btn-icon"
                title="Delete"
                @click="onDeleteWidget($event, widget.id)"
              >
                <i class="pi pi-trash" style="font-size: 10px"></i>
              </button>
            </div>
          </div>

          <div v-if="openWidgets.includes(widget.id)" class="widget-body">
            <!-- Debug frame toggle -->
            <div class="widget-toolbar">
              <label
                class="flex gap-2"
                style="
                  align-items: center;
                  cursor: pointer;
                  font-size: 12px;
                  color: var(--text-secondary);
                "
              >
                <label class="toggle">
                  <input
                    type="checkbox"
                    v-model="widget.debug_frame"
                    @change="onSetDebugFrame(widget.id)"
                  />
                  <span class="toggle-slider"></span>
                </label>
                Show Debug Frame
              </label>
            </div>

            <!-- Widget properties -->
            <div v-for="(item, i2) in widget.table" :key="i2" class="field-row">
              <label class="field-label">{{ item.name }}</label>
              <div class="field-value">
                <template v-if="item.type === 'string'">
                  <template v-if="item.name === 'name'">
                    <span
                      class="mono"
                      style="color: var(--accent); font-size: 12px"
                      >{{ item.value }}</span
                    >
                  </template>
                  <template v-else-if="item.name === 'value'">
                    <select
                      class="ctrl"
                      v-model="item.value"
                      @change="onSensorChange(widget, item)"
                    >
                      <option value="">— none —</option>
                      <option
                        v-for="s in sensors"
                        :key="s.name"
                        :value="s.name"
                      >
                        {{ s.name }}
                      </option>
                    </select>
                  </template>
                  <template v-else>
                    <input
                      class="ctrl"
                      type="text"
                      v-model="item.value"
                      @input="onPropertyChange(widget.id, item)"
                    />
                  </template>
                </template>

                <template v-else-if="item.type === 'number'">
                  <input
                    class="ctrl ctrl-num"
                    type="number"
                    v-model.number="item.value"
                    @input="onPropertyChange(widget.id, item)"
                  />
                </template>

                <template v-else-if="item.type === 'color'">
                  <div class="color-field">
                    <input
                      type="color"
                      class="ctrl-color ctrl"
                      :value="'#' + (item.value || '000000').replace('#', '')"
                      @input="
                        item.value = $event.target.value;
                        onSetColorPicker(widget.id, item);
                      "
                    />
                    <input
                      class="ctrl"
                      type="text"
                      v-model="item.value"
                      @input="onSetColorPicker(widget.id, item)"
                      style="max-width: 120px"
                    />
                  </div>
                </template>

                <template v-else-if="item.type === 'rect'">
                  <RectEdit
                    :portrait="'portrait' === theme?.orientation"
                    :rect="item.value"
                    @update:modelValue="onUpdateRect(widget.id, item.value)"
                  />
                </template>

                <template v-else-if="item.type === 'clock'">
                  <div class="flex gap-2" style="align-items: center">
                    <input
                      class="ctrl ctrl-num"
                      type="number"
                      v-model.number="item.value"
                      min="0"
                      @input="onPropertyChange(widget.id, item)"
                    />
                    <span class="text-muted" style="font-size: 12px">ms</span>
                  </div>
                </template>

                <template v-else-if="item.type === 'font'">
                  <FontEdit
                    :value="widget.font_string"
                    @update:modelValue="
                      onFontChange(widget.id, widget.font_string)
                    "
                  />
                </template>

                <template v-else-if="item.type === 'list'">
                  <select
                    class="ctrl"
                    v-model="item.value"
                    @change="onPropertyChange(widget.id, item)"
                  >
                    <option v-for="opt in item.list" :key="opt" :value="opt">
                      {{ opt }}
                    </option>
                  </select>
                </template>

                <template v-else-if="item.type === 'boolean'">
                  <label class="toggle">
                    <input
                      type="checkbox"
                      v-model="item.value"
                      @change="onPropertyChange(widget.id, item)"
                    />
                    <span class="toggle-slider"></span>
                  </label>
                </template>

                <template v-else-if="item.type === 'image'">
                  <template v-if="widget.value">
                    <img
                      :src="
                        '/api/image?screen=' +
                        screen.id +
                        '&widget=' +
                        widget.id
                      "
                      style="
                        height: 40px;
                        border-radius: 4px;
                        border: 1px solid var(--border);
                        margin-right: 8px;
                      "
                    />
                    <button
                      class="btn btn-danger btn-sm"
                      @click="onDeleteImage($event, widget)"
                    >
                      Remove
                    </button>
                  </template>
                  <template v-else>
                    <FileUpload
                      mode="basic"
                      name="uploading"
                      :url="
                        '/api/upload_image?screen=' +
                        screen.id +
                        '&widget=' +
                        widget.id
                      "
                      accept="image/png"
                      :maxFileSize="1000000"
                      @upload="onUploadImage"
                      :auto="true"
                      chooseLabel="Upload PNG"
                    />
                  </template>
                </template>

                <template v-else>
                  <span class="mono text-muted" style="font-size: 12px">{{
                    item.value
                  }}</span>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
/*!
 * s1panel-gui - App.vue (redesigned)
 * Premium dark theme - optimized components
 */

import api from "@/common/api";

// ── Inline SimpleKnob component ────────────────────────────────
const SimpleKnob = {
  name: "SimpleKnob",
  props: { modelValue: Number, min: { default: 1 }, max: { default: 5 } },
  emits: ["update:modelValue", "change"],
  computed: {
    pct() {
      return (this.modelValue - this.min) / (this.max - this.min);
    },
    dashArray() {
      const c = 2 * Math.PI * 38;
      const filled = c * 0.75 * this.pct;
      const gap = c * 0.75 - filled;
      return `${filled} ${gap} ${c * 0.25}`;
    },
    rotation() {
      return -135 + this.pct * 270;
    },
  },
  methods: {
    dec() {
      if (this.modelValue > this.min) {
        this.$emit("update:modelValue", this.modelValue - 1);
        this.$emit("change");
      }
    },
    inc() {
      if (this.modelValue < this.max) {
        this.$emit("update:modelValue", this.modelValue + 1);
        this.$emit("change");
      }
    },
  },
  template: `
    <div class="knob-group" style="gap:6px">
      <div class="knob-value">{{ modelValue }}</div>
      <svg class="knob-svg" width="80" height="80" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="38" fill="none" stroke="var(--border-bright)" stroke-width="8"
                stroke-dasharray="179.6 59.9" stroke-dashoffset="-44.9" stroke-linecap="round"/>
        <circle cx="50" cy="50" r="38" fill="none" stroke="var(--accent)" stroke-width="8"
                :stroke-dasharray="dashArray" stroke-dashoffset="-44.9" stroke-linecap="round"
                style="transition:stroke-dasharray 0.2s"/>
      </svg>
      <div class="knob-btns">
        <button class="btn btn-ghost btn-sm btn-icon" @click="dec"><i class="pi pi-minus"></i></button>
        <button class="btn btn-ghost btn-sm btn-icon" @click="inc"><i class="pi pi-plus"></i></button>
      </div>
    </div>
  `,
};

// ── Widget table builder ───────────────────────────────────────
function make_widget_table(widget, infos) {
  const _table = [];
  widget.setup = infos.find((each) => widget.name === each.name);
  Object.getOwnPropertyNames(widget).forEach((key) => {
    const _obj = { name: key, value: widget[key] };
    if (widget.setup && widget.setup.fields) {
      const _fi = widget.setup.fields.find((f) => f.name === key);
      if (_fi) {
        const _s = _fi.value.split(":");
        if (_s.length > 1) {
          _obj.type = _s[0];
          if (_obj.type === "list") _obj.list = _s[1].split(",");
        } else {
          _obj.type = _fi.value;
        }
      }
    }
    if (
      !key.startsWith("debug_") &&
      key !== "name" &&
      key !== "sensor" &&
      key !== "setup" &&
      key !== "id" &&
      key !== "group" &&
      key !== "table" &&
      key !== "font_string"
    ) {
      _table.push(_obj);
    }
  });
  widget.font_string = { font: widget.font };
  widget.table = _table.sort((a, b) => a.name.localeCompare(b.name));
}

export default {
  components: { SimpleKnob },

  data() {
    return {
      connected: true,
      activeTab: "config",
      openWidgets: [],

      // confirm dialog state
      confirm: {
        show: false,
        header: "",
        message: "",
        acceptLabel: "Confirm",
        rejectLabel: "Cancel",
        danger: true,
        _accept: null,
        _reject: null,
      },

      // modals
      modal_settings: false,

      config_manager: {
        listen: null,
        poll: null,
        refresh: null,
        heartbeat: null,
        saving: false,
      },

      sensor_manage: {
        show: false,
        show_add: false,
        show_edit: false,
        list: [],
        sensors: [],
        picked: null,
        config_data: null,
        edit: null,
      },

      widget_manage: { show: false, name: null },

      led_manage: {
        show: false,
        intensity: 3,
        speed: 3,
        theme: 2,
        list: [
          { id: 1, name: "Rainbow", icon: "pi pi-palette" },
          { id: 2, name: "Breathing", icon: "pi pi-heart-fill" },
          { id: 3, name: "Color Cycle", icon: "pi pi-sync" },
          { id: 5, name: "Automatic", icon: "pi pi-bolt" },
          { id: 4, name: "Off", icon: "pi pi-power-off" },
        ],
      },

      screen_manage: { show: false, name: null, active: 0 },

      // app state
      config: null,
      theme: null,
      screen: null,
      widgets: null,
      sensors: null,
      timeout: null,

      edit_theme: null,
      edit_screen: null,
      edit_refresh: null,
      edit_orientation: null,
      edit_duration: null,
      edit_background: null,
      edit_screen_name: null,
      unsaved_changes: false,
    };
  },

  computed: {
    shortThemeName() {
      if (!this.config || !this.theme) return "—";
      const found = this.config.theme_list?.find(
        (t) => t.config === this.config.theme,
      );
      const name = found?.name || this.config.theme || "—";
      return name.length > 18 ? name.slice(0, 16) + "…" : name;
    },
  },

  mounted() {
    this._canvas = this.$refs.canvas;
    this._ctx = this._canvas.getContext("2d");

    return Promise.all([
      api.fetch_config(),
      api.fetch_theme(),
      api.fetch_widgets(),
      api.fetch_sensors(),
      api.fetch_screen(),
    ]).then(([config, theme, widgets, sensors, screenInfo]) => {
      this.config = config;
      this.theme = theme;
      this.widgets = widgets;
      this.sensors = sensors;

      this.screen = theme.screens.find((s) => s.id === screenInfo.id);

      this.edit_theme = config.theme;
      this.edit_orientation = theme.orientation;
      this.edit_refresh = theme.refresh;
      this.edit_screen = this.screen.id;
      this.edit_duration = this.screen.duration || 0;
      this.edit_background = this.screen.background || "#000000";
      this.edit_screen_name = this.screen.name || "";

      this.unsaved_changes = config.unsaved_changes || false;

      this._canvas.width = theme.orientation === "portrait" ? 170 : 320;
      this._canvas.height = theme.orientation === "portrait" ? 320 : 170;

      api.set_poll_time(config.poll);

      this.screen.widgets.forEach((w) => make_widget_table(w, this.widgets));

      this.startRefresh();
    });
  },

  beforeUnmount() {
    clearTimeout(this.timeout);
  },

  methods: {
    // ── Preview refresh ──────────────────────────────────────────
    startRefresh() {
      api
        .load_image()
        .then(
          (img) => {
            if (!this.connected) return window.location.reload();
            this._ctx.reset();
            if (this.theme?.orientation === "portrait") {
              this._ctx.translate(170, 0);
              this._ctx.rotate(Math.PI / 2);
            }
            this._ctx.drawImage(img, 0, 0);
            this.connected = true;
          },
          () => {
            this.connected = false;
          },
        )
        .finally(() => {
          this.timeout = setTimeout(this.startRefresh, 1000);
        });
    },

    // ── Confirm dialog helper ────────────────────────────────────
    showConfirm({
      header,
      message,
      acceptLabel = "Confirm",
      rejectLabel = "Cancel",
      danger = true,
    }) {
      return new Promise((resolve, reject) => {
        this.confirm = {
          show: true,
          header,
          message,
          acceptLabel,
          rejectLabel,
          danger,
          _accept: resolve,
          _reject: reject,
        };
      });
    },
    confirmAccept() {
      this.confirm.show = false;
      this.confirm._accept?.();
    },
    confirmReject() {
      this.confirm.show = false;
      this.confirm._reject?.();
    },

    // ── Widget accordion ─────────────────────────────────────────
    toggleWidget(id) {
      const idx = this.openWidgets.indexOf(id);
      if (idx === -1) this.openWidgets.push(id);
      else this.openWidgets.splice(idx, 1);
    },

    // ── Widget editing ───────────────────────────────────────────
    onSetColorPicker(id, item) {
      if (!item.value.startsWith("#")) item.value = "#" + item.value;
      return api
        .update_property(this.screen.id, id, item.name, item.value)
        .then(() => {
          this.unsaved_changes = true;
        });
    },
    onSetDebugFrame(id) {
      return api.toggle_debug_frame(this.screen.id, id).then(() => {
        this.unsaved_changes = true;
      });
    },
    onUpdateRect(id, value) {
      return api.adjust_rect(this.screen.id, id, value).then(() => {
        this.unsaved_changes = true;
      });
    },
    onPropertyChange(id, item) {
      return api
        .update_property(this.screen.id, id, item.name, item.value)
        .then(() => {
          this.unsaved_changes = true;
        });
    },
    onSensorChange(widget, item) {
      const _isSensor = this.sensors.find((s) => s.name === item.value);
      const _p = _isSensor
        ? api.set_sensor(this.screen.id, widget.id, _isSensor.name)
        : api.update_property(this.screen.id, widget.id, item.name, item.value);
      return _p.then((r) => {
        widget.value = r.value;
        this.unsaved_changes = true;
      });
    },
    onFontChange(id, value) {
      return api
        .update_property(this.screen.id, id, "font", value.font)
        .then(() => {
          this.unsaved_changes = true;
        });
    },

    // ── Screen settings ──────────────────────────────────────────
    onSetBackground() {
      if (!this.edit_background.startsWith("#"))
        this.edit_background = "#" + this.edit_background;
      return api
        .set_background(this.screen.id, this.edit_background)
        .then((r) => {
          this.screen.background = r.value;
          this.unsaved_changes = true;
        });
    },
    onSetScreenName() {
      return api
        .set_screen_name(this.screen.id, this.edit_screen_name)
        .then(() => {
          this.screen.name = this.edit_screen_name;
          this.unsaved_changes = true;
        });
    },
    onSetScreenDuration() {
      return api
        .set_screen_duration(this.screen.id, this.edit_duration)
        .then(() => {
          this.screen.duration = this.edit_duration;
          this.unsaved_changes = true;
        });
    },
    onOrientationChange() {
      return api.set_orientation(this.edit_orientation).then(() => {
        this._canvas.width = this.edit_orientation === "portrait" ? 170 : 320;
        this._canvas.height = this.edit_orientation === "portrait" ? 320 : 170;
        this.theme.orientation = this.edit_orientation;
        this.unsaved_changes = true;
      });
    },
    onRefreshChange() {
      return api.set_refresh(this.edit_refresh).then(() => {
        this.theme.refresh = this.edit_refresh;
        this.unsaved_changes = true;
      });
    },
    onThemeChange() {
      if (this.config.theme_list.length > 1) {
        api.fetch_config_dirty().then((r) => {
          if (r.unsaved_changes) {
            this.showConfirm({
              header: "Unsaved Changes",
              message:
                "Switching themes will discard any unsaved changes. Continue?",
              acceptLabel: "Switch",
            })
              .then(() => {})
              .catch(() => {});
          }
        });
      }
    },
    onScreenChange() {
      return api.next_screen(this.edit_screen).then((r) => {
        this.screen = this.theme.screens.find((s) => s.id === r.id);
        if (this.screen) {
          this.edit_screen = this.screen.id;
          this.edit_duration = this.screen.duration || 0;
          this.edit_background = this.screen.background || "#000000";
          this.edit_screen_name = this.screen.name || "";
          this.screen.widgets.forEach((w) =>
            make_widget_table(w, this.widgets),
          );
        }
      });
    },

    // ── Screen manage ────────────────────────────────────────────
    onOpenScreenManage() {
      api.fetch_screen().then((r) => {
        this.screen_manage.name = "";
        this.screen_manage.active = r.id;
        this.screen_manage.show = true;
      });
    },
    onAddScreen() {
      return api.add_screen(this.screen_manage.name).then((r) => {
        if (r) {
          this.theme.screens.push(r);
          this.unsaved_changes = true;
        }
        this.screen_manage.name = "";
      });
    },
    onDeleteScreen(event, id) {
      this.showConfirm({
        header: "Delete Screen",
        message: "Delete this screen permanently?",
      })
        .then(() =>
          api.remove_screen(id).then(() => {
            this.theme.screens = this.theme.screens.filter((s) => s.id !== id);
            this.unsaved_changes = true;
          }),
        )
        .catch(() => {});
    },

    // ── Widget manage ────────────────────────────────────────────
    onShowAddWidget() {
      this.widget_manage.name = null;
      this.widget_manage.show = true;
    },
    onAddWidget() {
      return api
        .add_widget(this.screen.id, this.widget_manage.name)
        .then((r) => {
          if (r) {
            make_widget_table(r, this.widgets);
            this.screen.widgets.push(r);
            this.widget_manage.show = false;
          }
        });
    },
    onDeleteWidget(event, id) {
      this.showConfirm({
        header: "Delete Widget",
        message: "Remove this widget from the screen?",
      })
        .then(() =>
          api.delete_widget(this.screen.id, id).then(() => {
            this.screen.widgets = this.screen.widgets.filter(
              (w) => w.id !== id,
            );
            this.unsaved_changes = true;
          }),
        )
        .catch(() => {});
    },

    // ── Image / wallpaper ────────────────────────────────────────
    onUploadImage(data) {
      const r = JSON.parse(data.xhr.response);
      const w = this.screen.widgets.find((w) => w.id === r.widget);
      if (w) w.value = r.value;
    },
    onUploadWallpaper(data) {
      const r = JSON.parse(data.xhr.response);
      this.screen.wallpaper = r.value;
    },
    onDeleteWallpaper(event) {
      this.showConfirm({
        header: "Remove Wallpaper",
        message: "Clear wallpaper from this screen?",
      })
        .then(() =>
          api.clear_wallpaper(this.screen.id).then(() => {
            this.screen.wallpaper = null;
            this.unsaved_changes = true;
          }),
        )
        .catch(() => {});
    },
    onDeleteImage(event, widget) {
      this.showConfirm({
        header: "Remove Image",
        message: "Clear image from this widget?",
      })
        .then(() =>
          api.clear_image(this.screen.id, widget.id).then(() => {
            widget.value = null;
            this.unsaved_changes = true;
          }),
        )
        .catch(() => {});
    },

    // ── Settings ─────────────────────────────────────────────────
    onEditConfig() {
      this.config_manager.listen = this.config.listen;
      this.config_manager.poll = this.config.poll;
      this.config_manager.refresh = this.config.refresh;
      this.config_manager.heartbeat = this.config.heartbeat;
      this.modal_settings = true;
    },
    onSaveConfig() {
      this.config_manager.saving = true;
      return api
        .save_config({
          listen: this.config_manager.listen,
          poll: this.config_manager.poll,
          refresh: this.config_manager.refresh,
          heartbeat: this.config_manager.heartbeat,
        })
        .then(
          () => {
            Object.assign(this.config, this.config_manager);
            api.set_poll_time(this.config.poll);
            this.config_manager.saving = false;
            this.modal_settings = false;
          },
          () => {
            this.config_manager.saving = false;
          },
        );
    },

    // ── Theme save / revert ──────────────────────────────────────
    onSaveTheme() {
      return api.theme_save().then(() => {
        this.unsaved_changes = false;
      });
    },
    onRevertTheme() {
      return api.theme_revert().then((theme) => {
        this.theme = theme;
        this.screen = theme.screens[0];
        this.edit_orientation = theme.orientation;
        this.edit_refresh = theme.refresh;
        this.edit_screen = this.screen.id;
        this.edit_duration = this.screen.duration || 0;
        this.edit_background = this.screen.background || "#000000";
        this.edit_screen_name = this.screen.name || "";
        this.screen.widgets.forEach((w) => make_widget_table(w, this.widgets));
        this._canvas.width = theme.orientation === "portrait" ? 170 : 320;
        this._canvas.height = theme.orientation === "portrait" ? 320 : 170;
        this.unsaved_changes = false;
      });
    },

    // ── Sensor manage ────────────────────────────────────────────
    onOpenSensorManage() {
      api.config_sensor_list().then((r) => {
        this.sensor_manage.list = r;
        this.sensor_manage.show = true;
      });
    },
    onOpenAddSensor() {
      api.config_sensor_scan().then((r) => {
        this.sensor_manage.sensors = r
          .filter((s) => s.multiple)
          .map((s) => ({
            id: s.name,
            name: s.name + " — " + s.description,
            data: s,
          }));
        this.sensor_manage.picked = null;
        this.sensor_manage.config_data = null;
        this.sensor_manage.show_add = true;
      });
    },
    onSensorAddChange() {
      const found = this.sensor_manage.sensors.find(
        (s) => s.id === this.sensor_manage.picked,
      );
      if (found) this.sensor_manage.config_data = found.data;
    },
    onAddSensor() {
      const found = this.sensor_manage.sensors.find(
        (s) => s.id === this.sensor_manage.picked,
      );
      if (!found) {
        this.sensor_manage.show_add = false;
        return;
      }
      const cfg = Object.fromEntries(
        found.data.fields.map((f) => [f.name, f.value]),
      );
      api.config_sensor_add(found.data.module, cfg).then((r) => {
        if (r.status !== "success") {
          this.showConfirm({
            header: "Add Sensor Error",
            message: r.error,
            acceptLabel: null,
            rejectLabel: "OK",
            danger: true,
          }).catch(() => {});
        } else {
          Promise.all([api.config_sensor_list(), api.fetch_sensors()]).then(
            ([list, sensors]) => {
              this.sensor_manage.list = list;
              this.sensors = sensors;
              this.sensor_manage.show_add = false;
            },
          );
        }
      });
    },
    onSensorRemove(data) {
      this.showConfirm({
        header: "Remove Sensor",
        message: `Remove "${data.name}" sensor instance?`,
      })
        .then(() => {
          api.config_sensor_remove(data.name, data.info.module).then((r) => {
            if (r.status !== "success") {
              this.showConfirm({
                header: "Remove Error",
                message: r.error,
                acceptLabel: null,
                rejectLabel: "OK",
              }).catch(() => {});
            } else {
              Promise.all([api.config_sensor_list(), api.fetch_sensors()]).then(
                ([list, sensors]) => {
                  this.sensor_manage.list = list;
                  this.sensors = sensors;
                },
              );
            }
          });
        })
        .catch(() => {});
    },
    onSensorEdit(data) {
      const s = JSON.parse(JSON.stringify(data));
      s.info.fields.forEach((f) => {
        if (s.config.hasOwnProperty(f.name)) f.value = s.config[f.name];
      });
      this.sensor_manage.edit = s;
      this.sensor_manage.show_edit = true;
    },
    onSensorSave() {
      const s = this.sensor_manage.edit;
      if (!s) return;
      s.info.fields.forEach((f) => {
        if (s.config.hasOwnProperty(f.name)) s.config[f.name] = f.value;
      });
      api.config_sensor_edit(s.name, s.info.module, s.config).then((r) => {
        if (r.status !== "success") {
          this.showConfirm({
            header: "Edit Error",
            message: r.error,
            acceptLabel: null,
            rejectLabel: "OK",
          }).catch(() => {});
        } else {
          Promise.all([api.config_sensor_list(), api.fetch_sensors()]).then(
            ([list, sensors]) => {
              this.sensor_manage.list = list;
              this.sensors = sensors;
              this.sensor_manage.show_edit = false;
            },
          );
        }
      });
    },

    // ── LED ──────────────────────────────────────────────────────
    onOpenLED() {
      api.get_led_strip().then((r) => {
        this.led_manage.theme = r.theme;
        this.led_manage.intensity = r.intensity;
        this.led_manage.speed = r.speed;
        this.led_manage.show = true;
      });
    },
    onChangeLED() {
      return api
        .set_led_strip(
          this.led_manage.theme,
          this.led_manage.intensity,
          this.led_manage.speed,
          this.screen.id,
        )
        .then(() => {
          this.unsaved_changes = true;
        });
    },

    // ── Widget order ─────────────────────────────────────────────
    isFirst(id) {
      return this.screen.widgets[0].id === id;
    },
    isLast(id) {
      return this.screen.widgets[this.screen.widgets.length - 1].id === id;
    },
    onSwapUp(id, index) {
      return api.up_widget(this.screen.id, id).then(() => {
        let prev = null;
        this.screen.widgets.find((w) => {
          if (prev && w.id === id) {
            w.id = [prev.id, (prev.id = w.id)][0];
            return true;
          }
          prev = w;
        });
        this.screen.widgets.sort((a, b) => a.id - b.id);
        this.unsaved_changes = true;
      });
    },
    onSwapDown(id, index) {
      return api.down_widget(this.screen.id, id).then(() => {
        let prev = null;
        this.screen.widgets.find((w) => {
          if (prev && prev.id === id) {
            w.id = [prev.id, (prev.id = w.id)][0];
            return true;
          }
          prev = w;
        });
        this.screen.widgets.sort((a, b) => a.id - b.id);
        this.unsaved_changes = true;
      });
    },
    onSwapTop(id, index) {
      return api.top_widget(this.screen.id, id).then(() => {
        let c = 2;
        this.screen.widgets.forEach((w) => {
          w.id = w.id === id ? 1 : c++;
        });
        this.screen.widgets.sort((a, b) => a.id - b.id);
        this.unsaved_changes = true;
      });
    },
    onSwapBottom(id, index) {
      return api.bottom_widget(this.screen.id, id).then(() => {
        let c = 1;
        this.screen.widgets.forEach((w) => {
          w.id = w.id === id ? this.screen.widgets.length : c++;
        });
        this.screen.widgets.sort((a, b) => a.id - b.id);
        this.unsaved_changes = true;
      });
    },
  },
};
</script>
