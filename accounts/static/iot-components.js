/**
 * IoT Machine Control - Reusable UI Components
 * Vanilla JavaScript component library
 */

class MachineToggleComponent {
    /**
     * Create a machine toggle switch component
     * @param {HTMLElement} container - Parent container
     * @param {Object} config - Configuration object
     */
    constructor(container, config = {}) {
        this.container = container;
        this.machines = config.machines || [];
        this.onToggle = config.onToggle || (() => {});
        this.onReset = config.onReset || (() => {});
        
        this.init();
    }

    init() {
        this.render();
        this.attachEventListeners();
    }

    render() {
        this.container.innerHTML = `
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px;">
                ${this.machines.map(machine => this.createMachineCard(machine)).join('')}
            </div>
        `;
    }

    createMachineCard(machine) {
        const statusClass = machine.status === 'active' ? 'active' : 'inactive';
        const statusText = machine.status.charAt(0).toUpperCase() + machine.status.slice(1);
        const icon = machine.icon || 'fa-cogs';
        const power = machine.power || 0;
        const temp = machine.temp || 0;
        const uptime = machine.uptime || '0h 0m';
        
        return `
            <div class="iot-machine-card ${statusClass}" data-machine-id="${machine.id}">
                <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <i class="fas ${icon}" style="font-size: 20px; color: #0066cc;"></i>
                        <span style="font-weight: 600;">${machine.name}</span>
                    </div>
                    <span style="padding: 4px 10px; border-radius: 15px; font-size: 11px; font-weight: 600; background: ${statusClass === 'active' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(107, 114, 128, 0.2)'}; color: ${statusClass === 'active' ? '#10b981' : '#9ca3af'};">
                        <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: ${statusClass === 'active' ? '#10b981' : '#6b7280'}; margin-right: 4px;"></span>
                        ${statusText}
                    </span>
                </div>
                
                <div style="text-align: center; margin: 25px 0;">
                    <div style="display: inline-block; width: 100px; height: 50px; background: ${statusClass === 'active' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(107, 114, 128, 0.2)'}; border: 2px solid ${statusClass === 'active' ? '#10b981' : '#6b7280'}; border-radius: 25px; cursor: pointer; position: relative; transition: all 0.3s ease;" class="iot-toggle" data-machine-id="${machine.id}">
                        <div style="position: absolute; top: 2px; left: ${statusClass === 'active' ? 'calc(100% - 44px)' : '2px'}; width: 40px; height: 40px; border-radius: 50%; background: ${statusClass === 'active' ? '#10b981' : '#6b7280'}; transition: all 0.3s ease; display: flex; align-items: center; justify-content: center; color: white; font-weight: 600;">
                            ${statusClass === 'active' ? '✓' : '✕'}
                        </div>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; padding: 12px; background: rgba(255, 255, 255, 0.03); border-radius: 6px; border: 1px solid #334155; margin: 15px 0;">
                    <div style="text-align: center;">
                        <div style="font-size: 10px; color: #cbd5e1; margin-bottom: 3px; text-transform: uppercase;">Power</div>
                        <div style="font-size: 14px; font-weight: 600;">${power} W</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 10px; color: #cbd5e1; margin-bottom: 3px; text-transform: uppercase;">Temp</div>
                        <div style="font-size: 14px; font-weight: 600; color: ${temp > 60 ? '#ef4444' : '#f1f5f9'};">${temp}°C</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 10px; color: #cbd5e1; margin-bottom: 3px; text-transform: uppercase;">Uptime</div>
                        <div style="font-size: 14px; font-weight: 600;">${uptime}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 10px; color: #cbd5e1; margin-bottom: 3px; text-transform: uppercase;">Status</div>
                        <div style="font-size: 14px; font-weight: 600;">${statusClass === 'active' ? '🟢' : '⚫'}</div>
                    </div>
                </div>
                
                <div style="display: flex; gap: 8px; margin-top: 12px;">
                    <button class="iot-btn-action" data-action="details" data-machine-id="${machine.id}" style="flex: 1; padding: 8px; background: rgba(255, 255, 255, 0.1); border: 1px solid #334155; color: #f1f5f9; border-radius: 5px; cursor: pointer; font-size: 11px; font-weight: 600; text-transform: uppercase; transition: all 0.2s ease;">
                    <i class="fas fa-info-circle"></i> Details
                    </button>
                    <button class="iot-btn-reset" data-machine-id="${machine.id}" style="flex: 1; padding: 8px; background: rgba(255, 255, 255, 0.1); border: 1px solid #334155; color: #f1f5f9; border-radius: 5px; cursor: pointer; font-size: 11px; font-weight: 600; text-transform: uppercase; transition: all 0.2s ease;">
                    <i class="fas fa-redo"></i> Reset
                    </button>
                </div>
            </div>
        `;
    }

    attachEventListeners() {
        this.container.querySelectorAll('.iot-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                const machineId = parseInt(e.currentTarget.dataset.machineId);
                this.onToggle(machineId);
            });
        });

        this.container.querySelectorAll('.iot-btn-reset').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const machineId = parseInt(e.currentTarget.dataset.machineId);
                this.onReset(machineId);
            });
        });

        this.container.querySelectorAll('.iot-btn-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const machineId = parseInt(e.currentTarget.dataset.machineId);
                const machine = this.machines.find(m => m.id === machineId);
                alert(`${machine.name}\nStatus: ${machine.status}\nPower: ${machine.power}W\nTemp: ${machine.temp}°C`);
            });
        });
    }

    updateMachine(machineId, updates) {
        const machine = this.machines.find(m => m.id === machineId);
        if (machine) {
            Object.assign(machine, updates);
            this.render();
            this.attachEventListeners();
        }
    }
}

class StatsComponent {
    /**
     * Create a statistics component
     * @param {HTMLElement} container
     * @param {Object[]} machines
     */
    constructor(container, machines) {
        this.container = container;
        this.machines = machines;
        this.render();
    }

    render() {
        const active = this.machines.filter(m => m.status === 'active').length;
        const power = this.machines.reduce((s, m) => s + (m.power || 0), 0);
        const temp = Math.round(this.machines.reduce((s, m) => s + (m.temp || 0), 0) / this.machines.length);

        this.container.innerHTML = `
            <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                <div style="padding: 12px 18px; background: rgba(255, 255, 255, 0.05); border-radius: 8px; border: 1px solid #334155; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 11px; color: #cbd5e1;">Active Machines</span>
                    <span style="font-size: 18px; font-weight: 600;">${active}</span>
                </div>
                <div style="padding: 12px 18px; background: rgba(255, 255, 255, 0.05); border-radius: 8px; border: 1px solid #334155; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 11px; color: #cbd5e1;">Total Power</span>
                    <span style="font-size: 18px; font-weight: 600;">${power} W</span>
                </div>
                <div style="padding: 12px 18px; background: rgba(255, 255, 255, 0.05); border-radius: 8px; border: 1px solid #334155; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 11px; color: #cbd5e1;">Avg Temperature</span>
                    <span style="font-size: 18px; font-weight: 600;">${temp}°C</span>
                </div>
            </div>
        `;
    }

    update(machines) {
        this.machines = machines;
        this.render();
    }
}

class ConfirmationModal {
    /**
     * Create a confirmation modal
     * @param {Object} options
     */
    constructor(options = {}) {
        this.title = options.title || 'Confirm';
        this.message = options.message || 'Are you sure?';
        this.onConfirm = options.onConfirm || (() => {});
        this.create();
    }

    create() {
        this.modal = document.createElement('div');
        this.modal.innerHTML = `
            <div style="position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); display: none; align-items: center; justify-content: center;" id="iot-modal">
                <div style="background: #1e293b; padding: 25px; border-radius: 10px; border: 2px solid #334155; max-width: 350px; width: 90%;">
                    <div style="font-size: 16px; font-weight: 600; margin-bottom: 12px; color: #f1f5f9;">
                        <i class="fas fa-exclamation-circle" style="color: #f59e0b; margin-right: 8px;"></i>
                        ${this.title}
                    </div>
                    <div style="margin: 15px 0; color: #cbd5e1; font-size: 14px;">
                        ${this.message}
                    </div>
                    <div style="display: flex; gap: 8px; margin-top: 20px;">
                        <button onclick="document.getElementById('iot-modal').style.display = 'none';" style="flex: 1; padding: 10px; background: rgba(255, 255, 255, 0.1); border: 1px solid #334155; color: #f1f5f9; border-radius: 5px; cursor: pointer; font-weight: 600; text-transform: uppercase; font-size: 11px;">
                            Cancel
                        </button>
                        <button id="iot-confirm-btn" style="flex: 1; padding: 10px; background: #10b981; border: none; color: white; border-radius: 5px; cursor: pointer; font-weight: 600; text-transform: uppercase; font-size: 11px;">
                            Confirm
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(this.modal);
    }

    show() {
        document.getElementById('iot-modal').style.display = 'flex';
        document.getElementById('iot-confirm-btn').onclick = () => {
            this.onConfirm();
            document.getElementById('iot-modal').style.display = 'none';
        };
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        MachineToggleComponent,
        StatsComponent,
        ConfirmationModal
    };
}
